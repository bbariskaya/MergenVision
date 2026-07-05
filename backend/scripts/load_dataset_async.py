#!/usr/bin/env python3
"""High-throughput async dataset loader.

Decouples GPU inference from persistence so that inference can run at close to
ML-only throughput (~300 img/s). Inference and persistence overlap: while chunk
N+1 is being processed on the GPU, chunk N is being written to PostgreSQL,
MinIO and Qdrant.

Supported datasets:
    - celeba: identity_CelebA.txt + img_align_celeba/ directory
    - lfw:    lfw-deepfunneled/lfw-deepfunneled/ directory structure

Usage inside a backend container::

    uv run python scripts/load_dataset_async.py \
        --dataset celeba \
        --images-dir /datasets/celeba/img_align_celeba \
        --identity-file /datasets/celeba/identity_CelebA.txt \
        --chunk-size 64

    uv run python scripts/load_dataset_async.py \
        --dataset lfw \
        --lfw-dir /datasets/lfw/lfw-deepfunneled/lfw-deepfunneled \
        --chunk-size 64
"""

from __future__ import annotations

import argparse
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.ids import new_uuid7
from app.core.security import hash_national_id, mask_national_id
from app.domain.models import FaceIdentity, FaceSample, Person, PersonPhoto
from app.infrastructure.adapters.base import EnrollOutput, ImageValidationResult
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.db import AsyncSessionLocal
from app.infrastructure.storage import UploadItem, get_object_storage
from app.infrastructure.vector_store import VectorStore, collection_name, get_vector_store
from app.repositories.audit_repo import AuditRepository
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository


@dataclass
class PendingItem:
    """Dataset item before it is loaded into memory."""

    path: Path
    external_identity: str
    person_id: UUID


@dataclass
class LoadedItem:
    """Dataset item loaded and validated, ready for inference."""

    pending: PendingItem
    image_bytes: bytes
    validation: ImageValidationResult


@dataclass
class Stats:
    """Thread-safe loader statistics."""

    identities: int = 0
    photos: int = 0
    faces: int = 0
    samples: int = 0
    errors: int = 0
    chunks: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add(self, photos: int, faces: int, samples: int) -> None:
        async with self.lock:
            self.photos += photos
            self.faces += faces
            self.samples += samples
            self.chunks += 1

    async def add_error(self) -> None:
        async with self.lock:
            self.errors += 1


def _person_from_external_id(external_id: str, source: str) -> Person:
    """Build a Person row for an external dataset identity."""
    return Person(
        firstName=None,
        lastName=None,
        nationalIdHash=hash_national_id(external_id),
        nationalIdMasked=mask_national_id(external_id),
        details={"source": source, "external_id": external_id},
    )


async def _create_persons(
    session: Any,
    external_ids: list[str],
    source: str,
    person_chunk_size: int = 200,
) -> dict[str, UUID]:
    """Bulk insert missing dataset identities and return external_id -> personId."""
    repo = PersonRepository(session)

    # Detect already-existing persons by national id hash.
    hashes = {eid: hash_national_id(eid) for eid in external_ids}
    existing_stmt = select(
        Person.personId,
        Person.nationalIdHash,
    ).where(
        Person.nationalIdHash.in_(list(hashes.values())),
        Person.isActive.is_(True),
    )
    existing_rows = await session.execute(existing_stmt)
    hash_to_person_id = {
        row.nationalIdHash: row.personId for row in existing_rows.mappings().all()
    }
    mapping = {
        eid: hash_to_person_id[h]
        for eid, h in hashes.items()
        if h in hash_to_person_id
    }

    # Insert only the missing ones.
    new_ids = [eid for eid in external_ids if eid not in mapping]
    for i in range(0, len(new_ids), person_chunk_size):
        chunk_ids = new_ids[i : i + person_chunk_size]
        persons = [_person_from_external_id(eid, source) for eid in chunk_ids]
        try:
            await repo.bulk_create(persons)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Failed to bulk insert persons chunk {i // person_chunk_size} "
                f"(size {len(persons)}): {exc.__class__.__name__}: {exc}"
            ) from exc
        for person, eid in zip(persons, chunk_ids, strict=True):
            mapping[eid] = person.personId  # type: ignore[union-attr]

    await session.commit()
    return mapping


def _parse_celeba_mapping(identity_file: Path, images_dir: Path) -> dict[str, list[Path]]:
    """Return external_identity -> list[image_path]."""
    groups: dict[str, list[Path]] = defaultdict(list)
    with identity_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            filename, identity = parts
            groups[identity].append(images_dir / filename)
    return dict(groups)


def _parse_lfw_mapping(lfw_dir: Path) -> dict[str, list[Path]]:
    """Return directory name -> list[image_path]."""
    groups: dict[str, list[Path]] = {}
    for identity_dir in sorted(lfw_dir.iterdir()):
        if identity_dir.is_dir():
            groups[identity_dir.name] = sorted(identity_dir.glob("*.jpg"))
    return groups


def _pending_items(
    groups: dict[str, list[Path]],
    person_map: dict[str, UUID],
) -> list[PendingItem]:
    items: list[PendingItem] = []
    for external_id, paths in groups.items():
        person_id = person_map[external_id]
        for path in paths:
            items.append(PendingItem(path, external_id, person_id))
    return items


def _load_one(pipeline: FacePipeline, item: PendingItem) -> LoadedItem:
    data = item.path.read_bytes()
    validation = pipeline.validate(data)
    return LoadedItem(item, data, validation)


async def _read_chunk(
    pipeline: FacePipeline,
    chunk: list[PendingItem],
) -> list[LoadedItem]:
    """Read and validate a chunk of images concurrently."""
    return await asyncio.gather(
        *[asyncio.to_thread(_load_one, pipeline, item) for item in chunk],
        return_exceptions=True,
    )


def _filter_loaded(
    results: list[LoadedItem | BaseException],
    stats: Stats,
) -> list[LoadedItem]:
    loaded: list[LoadedItem] = []
    for result in results:
        if isinstance(result, Exception):
            asyncio.create_task(stats.add_error())
            continue
        loaded.append(result)
    return loaded


async def producer(
    pending_chunks: list[list[PendingItem]],
    queue: asyncio.Queue[list[LoadedItem] | None],
    pipeline: FacePipeline,
    stats: Stats,
) -> None:
    """Feed loaded and validated chunks into the inference queue."""
    for chunk in pending_chunks:
        raw = await _read_chunk(pipeline, chunk)
        loaded = _filter_loaded(raw, stats)
        if loaded:
            await queue.put(loaded)
    await queue.put(None)


async def inference_worker(
    input_queue: asyncio.Queue[list[LoadedItem] | None],
    output_queue: asyncio.Queue[tuple[list[LoadedItem], list[list[EnrollOutput]]] | None],
    pipeline: FacePipeline,
) -> None:
    """Run GPU batch inference and hand results to persistence."""
    while True:
        loaded = await input_queue.get()
        if loaded is None:
            await output_queue.put(None)
            break
        image_bytes_list = [item.image_bytes for item in loaded]
        outputs = await asyncio.to_thread(pipeline.enroll_batch, image_bytes_list)
        await output_queue.put((loaded, outputs))


async def _persist_chunk(
    loaded: list[LoadedItem],
    outputs_per_image: list[list[EnrollOutput]],
    storage: Any,
    vector_store: VectorStore,
    settings: Any,
    stats: Stats,
) -> None:
    """Write one processed chunk to PostgreSQL, MinIO and Qdrant."""
    async with AsyncSessionLocal() as session:
        identity_repo = FaceIdentityRepository(session)
        photo_repo = PhotoRepository(session)
        sample_repo = FaceSampleRepository(session)

        # Flatten detections and create one FaceIdentity per face.
        indexed_outputs: list[tuple[int, EnrollOutput]] = []
        for img_idx, outputs in enumerate(outputs_per_image):
            for output in outputs:
                indexed_outputs.append((img_idx, output))

        faces_count = len(indexed_outputs)
        identities: list[FaceIdentity] = [
            FaceIdentity(
                faceId=new_uuid7(),
                identityType="known",
                personId=loaded[img_idx].pending.person_id,
                displayName=None,
            )
            for img_idx, _ in indexed_outputs
        ]
        if identities:
            await identity_repo.bulk_create_known(identities)

        # Prepare photos with pre-generated UUIDs and original uploads.
        photos: list[PersonPhoto] = []
        original_uploads: list[UploadItem] = []
        for item in loaded:
            photo_id = new_uuid7()
            key = f"{item.pending.person_id}/{photo_id}.jpg"
            photos.append(
                PersonPhoto(
                    photoId=photo_id,
                    personId=item.pending.person_id,
                    originalImageBucket=settings.minio_bucket_people_photos,
                    originalImageKey=key,
                    contentType=item.validation.content_type,
                    sizeBytes=len(item.image_bytes),
                    width=item.validation.width,
                    height=item.validation.height,
                )
            )
            original_uploads.append(
                UploadItem(
                    bucket=settings.minio_bucket_people_photos,
                    key=key,
                    data=item.image_bytes,
                    content_type=item.validation.content_type,
                )
            )

        # Prepare samples, crop uploads and Qdrant points.
        samples: list[FaceSample] = []
        crop_uploads: list[UploadItem] = []
        points: list[dict[str, Any]] = []

        for (img_idx, output), identity in zip(indexed_outputs, identities, strict=True):
            photo = photos[img_idx]
            sample_id = new_uuid7()
            qdrant_point_id = new_uuid7()
            crop_key = f"{identity.faceId}/{sample_id}.jpg"
            collection = collection_name(
                output.model_name,
                output.dimension,
                output.model_version,
                prefix=settings.qdrant_collection_prefix,
            )

            samples.append(
                FaceSample(
                    sampleId=sample_id,
                    faceId=identity.faceId,
                    photoId=photo.photoId,
                    qdrantPointId=qdrant_point_id,
                    collectionName=collection,
                    modelName=output.model_name,
                    modelVersion=output.model_version,
                    embeddingDimension=output.dimension,
                    qualityScore=output.quality_score,
                    cropImageBucket=settings.minio_bucket_face_crops,
                    cropImageKey=crop_key,
                    isIndexed=True,
                )
            )
            crop_uploads.append(
                UploadItem(
                    bucket=settings.minio_bucket_face_crops,
                    key=crop_key,
                    data=output.crop_bytes,
                    content_type="image/jpeg",
                )
            )
            points.append(
                {
                    "id": qdrant_point_id,
                    "vector": output.embedding,
                    "payload": {
                        "faceId": str(identity.faceId),
                        "personId": str(identity.personId),
                        "photoId": str(photo.photoId),
                        "sampleId": str(sample_id),
                        "identityType": identity.identityType,
                        "modelName": output.model_name,
                        "modelVersion": output.model_version,
                        "embeddingDimension": output.dimension,
                        "isActive": True,
                        "collectionName": collection,
                    },
                }
            )

        # Upload all objects for this chunk concurrently.
        if original_uploads:
            await storage.upload_concurrent(original_uploads)
        if crop_uploads:
            await storage.upload_concurrent(crop_uploads)

        # Bulk insert DB rows.
        await photo_repo.bulk_create(photos)
        if samples:
            await sample_repo.bulk_create(samples)

        # Upsert embeddings.
        if points:
            await vector_store.upsert_batch(points, batch_size=500)

        # Audit one entry per chunk instead of per image/identity.
        audit = AuditRepository(session)
        await audit.log(
            action="person.enroll.batch",
            entity_type="person",
            entity_id=None,
            actor=None,
            request_id=None,
            outcome="success",
            safe_metadata={
                "source": "async_loader",
                "chunkPhotos": len(photos),
                "chunkFaces": faces_count,
                "chunkSamples": len(samples),
            },
        )

        await session.commit()

    await stats.add(len(photos), faces_count, len(samples))


async def persist_worker(
    queue: asyncio.Queue[tuple[list[LoadedItem], list[list[EnrollOutput]]] | None],
    storage: Any,
    vector_store: VectorStore,
    settings: Any,
    stats: Stats,
) -> None:
    """Persist inferred chunks to durable storage."""
    while True:
        item = await queue.get()
        if item is None:
            break
        loaded, outputs = item
        try:
            await _persist_chunk(
                loaded, outputs, storage, vector_store, settings, stats
            )
        except Exception as exc:  # noqa: BLE001
            await stats.add_error()
            print(f"[PERSIST ERROR] {exc}")


def _chunk(items: list[PendingItem], size: int) -> list[list[PendingItem]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Async bulk dataset loader")
    parser.add_argument(
        "--dataset",
        choices=("celeba", "lfw"),
        required=True,
        help="Dataset format",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        help="Directory containing images (required for celeba)",
    )
    parser.add_argument(
        "--identity-file",
        type=Path,
        help="CelebA identity_CelebA.txt path (required for celeba)",
    )
    parser.add_argument(
        "--lfw-dir",
        type=Path,
        help="LFW root directory with identity subfolders (required for lfw)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=64,
        help="Images per inference chunk",
    )
    parser.add_argument(
        "--queue-size",
        type=int,
        default=2,
        help="Max number of chunks buffered between stages",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N images",
    )
    args = parser.parse_args()

    if args.dataset == "celeba" and (not args.images_dir or not args.identity_file):
        raise SystemExit("--images-dir and --identity-file are required for celeba")
    if args.dataset == "lfw" and not args.lfw_dir:
        raise SystemExit("--lfw-dir is required for lfw")

    settings = get_settings()
    face_pipeline = FacePipeline(settings=settings)
    storage = get_object_storage(settings=settings)
    vector_store = get_vector_store(settings=settings)

    await vector_store.ensure_collection(
        settings.recognizer_model_name,
        settings.recognizer_embedding_dimension,
        settings.recognizer_version,
    )

    # Parse dataset grouping: external identity -> image paths.
    if args.dataset == "celeba":
        groups = _parse_celeba_mapping(args.identity_file, args.images_dir)
        source = "celeba"
    else:
        groups = _parse_lfw_mapping(args.lfw_dir)
        source = "lfw"

    print(f"[DATASET] {args.dataset}: {len(groups)} identities")

    # Pre-create all persons with bulk inserts.
    async with AsyncSessionLocal() as session:
        person_map = await _create_persons(
            session,
            list(groups.keys()),
            source,
        )

    # Flatten to pending items, optionally limit.
    pending_items = _pending_items(groups, person_map)
    if args.limit:
        pending_items = pending_items[: args.limit]
    print(f"[LOAD] {len(pending_items)} images to process")

    pending_chunks = _chunk(pending_items, args.chunk_size)

    stats = Stats(identities=len(groups))
    infer_queue: asyncio.Queue[list[LoadedItem] | None] = asyncio.Queue(
        maxsize=args.queue_size
    )
    persist_queue: asyncio.Queue[
        tuple[list[LoadedItem], list[list[EnrollOutput]]] | None
    ] = asyncio.Queue(maxsize=args.queue_size)

    start = time.perf_counter()
    progress_task = asyncio.create_task(_progress_reporter(stats, start))

    producer_task = asyncio.create_task(
        producer(pending_chunks, infer_queue, face_pipeline, stats)
    )
    infer_task = asyncio.create_task(
        inference_worker(infer_queue, persist_queue, face_pipeline)
    )
    persist_task = asyncio.create_task(
        persist_worker(persist_queue, storage, vector_store, settings, stats)
    )

    await asyncio.gather(producer_task, infer_task, persist_task)

    progress_task.cancel()
    try:
        await progress_task
    except asyncio.CancelledError:
        pass

    total = time.perf_counter() - start
    print("\n=== Async Load Complete ===")
    print(f"identities : {stats.identities}")
    print(f"photos     : {stats.photos}")
    print(f"faces      : {stats.faces}")
    print(f"samples    : {stats.samples}")
    print(f"errors     : {stats.errors}")
    print(f"chunks     : {stats.chunks}")
    print(f"total_seconds: {total:.3f}")
    if stats.photos:
        print(f"img/s      : {stats.photos / total:.1f}")
    if stats.faces:
        print(f"face/s     : {stats.faces / total:.1f}")


async def _progress_reporter(stats: Stats, start: float) -> None:
    """Print throughput every 10 seconds."""
    while True:
        await asyncio.sleep(10)
        async with stats.lock:
            elapsed = time.perf_counter() - start
            photos = stats.photos
        if photos:
            print(
                f"[PROGRESS] {elapsed:.1f}s | photos={photos} | "
                f"img/s={photos / elapsed:.1f}"
            )


if __name__ == "__main__":
    asyncio.run(main())
