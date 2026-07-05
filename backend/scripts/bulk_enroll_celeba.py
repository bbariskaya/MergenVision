"""Bulk-enroll CelebA faces using host TensorRT engines.

Runs outside Docker, talks to the PostgreSQL/Qdrant/MinIO services exposed by
``docker-compose.yml`` on localhost ports, and writes data in batches so the
UI can browse the results.

Example:
    cd backend
    uv run python scripts/bulk_enroll_celeba.py \
        --dataset /home/user/MergenVision/testdatasets/img_align_celeba/img_align_celeba \
        --batch-size 64 \
        --max-images 10000

Environment:
    DATABASE_URL=postgresql+asyncpg://mergen:mergen@localhost:5433/mergenvision
    QDRANT_URL=http://localhost:6334
    MINIO_URL=localhost:9002
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin
    MINIO_SECURE=false
    TRT_ENGINE_DIR=/home/user/MergenVision/artifacts/trt_engines
    MODELS_DIR=/home/user/MergenVision/artifacts/model_benchmarks/models
    GPU_DEVICE_ID=0
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import os
import sys
import time
from pathlib import Path
from uuid import UUID

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

# Make ``app.*`` imports work when the script is run from ``backend/``.
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.ids import new_uuid7  # noqa: E402
from app.domain.models import FaceIdentity, FaceSample, Person, PersonPhoto  # noqa: E402
from app.infrastructure.adapters.base import EnrollOutput  # noqa: E402
from app.infrastructure.adapters.pipelines import FacePipeline  # noqa: E402
from app.infrastructure.db import get_async_session_maker, get_db_engine  # noqa: E402
from app.infrastructure.minio_client import get_minio_client  # noqa: E402
from app.infrastructure.qdrant_client import get_qdrant_client  # noqa: E402
from app.infrastructure.storage import ObjectStorage, UploadItem  # noqa: E402
from app.infrastructure.vector_store import VectorStore, collection_name  # noqa: E402
from app.repositories.face_identity_repo import FaceIdentityRepository  # noqa: E402
from app.repositories.face_sample_repo import FaceSampleRepository  # noqa: E402
from app.repositories.person_repo import PersonRepository  # noqa: E402
from app.repositories.photo_repo import PhotoRepository  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk-enroll CelebA into MergenVision")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("/home/user/MergenVision/testdatasets/img_align_celeba/img_align_celeba"),
        help="Directory containing aligned CelebA JPG images",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1024,
        help="Number of images per inference + persistence batch",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Max images to process (0 = all)",
    )
    parser.add_argument(
        "--gpu-device-id",
        type=int,
        default=int(os.getenv("GPU_DEVICE_ID", "0")),
        help="CUDA device id used by the pipeline",
    )
    parser.add_argument(
        "--min-face-quality",
        type=float,
        default=0.0,
        help="Drop faces whose detector score is below this threshold",
    )
    parser.add_argument(
        "--decoder-backend",
        choices=["auto", "dali", "pil"],
        default="auto",
        help="Image decoder backend used by FacePipeline",
    )
    return parser.parse_args()


def discover_images(dataset_dir: Path, max_images: int) -> list[Path]:
    if not dataset_dir.is_dir():
        raise SystemExit(f"Dataset directory not found: {dataset_dir}")
    images = sorted(dataset_dir.glob("*.jpg"))
    if not images:
        images = sorted(dataset_dir.glob("*.png"))
    if not images:
        raise SystemExit(f"No *.jpg/*.png images found in {dataset_dir}")
    if max_images > 0:
        images = images[:max_images]
    return images


def content_type_from_path(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(ext, "image/jpeg")


def read_image_batch(paths: list[Path]) -> list[bytes]:
    return [p.read_bytes() for p in paths]


def prepare_photos_and_uploads(
    settings: Settings,
    person_ids: list[UUID],
    image_paths: list[Path],
    image_bytes: list[bytes],
) -> tuple[list[PersonPhoto], list[UploadItem]]:
    photos: list[PersonPhoto] = []
    uploads: list[UploadItem] = []
    for person_id, path, data in zip(person_ids, image_paths, image_bytes, strict=True):
        photo_id = new_uuid7()
        key = f"{person_id}/{photo_id}.jpg"
        content_type = content_type_from_path(path)
        photos.append(
            PersonPhoto(
                photoId=photo_id,
                personId=person_id,
                originalImageBucket=settings.minio_bucket_people_photos,
                originalImageKey=key,
                contentType=content_type,
                sizeBytes=len(data),
                width=None,
                height=None,
            )
        )
        uploads.append(
            UploadItem(
                bucket=settings.minio_bucket_people_photos,
                key=key,
                data=data,
                content_type=content_type,
            )
        )
    return photos, uploads


def prepare_identities(person_ids: list[UUID], outputs_per_image: list[list[EnrollOutput]]) -> list[FaceIdentity]:
    identities: list[FaceIdentity] = []
    for person_id, outputs in zip(person_ids, outputs_per_image, strict=True):
        for _ in outputs:
            identities.append(
                FaceIdentity(
                    identityType="known",
                    personId=person_id,
                    displayName=None,
                )
            )
    return identities


def prepare_samples_and_points(
    settings: Settings,
    identities: list[FaceIdentity],
    photos: list[PersonPhoto],
    indexed_outputs: list[tuple[int, EnrollOutput]],
) -> tuple[list[FaceSample], list[UploadItem], list[dict]]:
    samples: list[FaceSample] = []
    uploads: list[UploadItem] = []
    points: list[dict] = []

    for identity, (img_idx, output) in zip(identities, indexed_outputs, strict=True):
        photo = photos[img_idx]
        sample_id = new_uuid7()
        qdrant_point_id = new_uuid7()
        crop_key = f"{identity.faceId}/{sample_id}.jpg"
        coll = collection_name(
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
                collectionName=coll,
                modelName=output.model_name,
                modelVersion=output.model_version,
                embeddingDimension=output.dimension,
                qualityScore=output.quality_score,
                cropImageBucket=settings.minio_bucket_face_crops,
                cropImageKey=crop_key,
                isIndexed=True,
            )
        )
        uploads.append(
            UploadItem(
                bucket=settings.minio_bucket_face_crops,
                key=crop_key,
                data=output.crop_bytes,
                content_type="image/jpeg",
            )
        )
        vector = output.embedding
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        points.append(
            {
                "id": qdrant_point_id,
                "vector": vector,
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
                },
            }
        )

    return samples, uploads, points


async def persist_batch(
    session: AsyncSession,
    storage: ObjectStorage,
    vector_store: VectorStore,
    person_ids: list[UUID],
    image_paths: list[Path],
    image_bytes: list[bytes],
    outputs_per_image: list[list[EnrollOutput]],
    settings: Settings,
) -> tuple[int, int, int]:
    """Insert one batch: persons, photos, identities, samples + MinIO + Qdrant."""
    # 1. Persons
    persons = [
        Person(
            firstName="CelebA",
            lastName=path.stem,
            details={"source": "celeba", "filename": path.name},
        )
        for path in image_paths
    ]
    person_repo = PersonRepository(session)
    await person_repo.bulk_create(persons)
    person_ids.clear()
    person_ids.extend([p.personId for p in persons])

    # 2. Photos + original uploads (MinIO and DB in parallel)
    photo_repo = PhotoRepository(session)
    photos, original_uploads = prepare_photos_and_uploads(
        settings, person_ids, image_paths, image_bytes
    )
    await asyncio.gather(
        storage.upload_concurrent(original_uploads),
        photo_repo.bulk_create(photos),
    )

    # 3. Face identities
    identity_repo = FaceIdentityRepository(session)
    identities = prepare_identities(person_ids, outputs_per_image)
    if identities:
        await identity_repo.bulk_create_known(identities)

    # 4. Samples + crop uploads + Qdrant points (all in parallel)
    indexed_outputs: list[tuple[int, EnrollOutput]] = []
    for img_idx, outputs in enumerate(outputs_per_image):
        for output in outputs:
            indexed_outputs.append((img_idx, output))

    sample_repo = FaceSampleRepository(session)
    samples: list[FaceSample] = []
    crop_uploads: list[UploadItem] = []
    points: list[dict] = []
    if identities:
        samples, crop_uploads, points = prepare_samples_and_points(
            settings, identities, photos, indexed_outputs
        )
        await asyncio.gather(
            storage.upload_concurrent(crop_uploads),
            sample_repo.bulk_create(samples),
            vector_store.upsert_batch(points, batch_size=500),
        )

    await session.commit()

    return len(persons), len(identities), len(samples)


async def run_enrollment(args: argparse.Namespace, settings: Settings) -> None:
    image_paths = discover_images(args.dataset, args.max_images)
    total = len(image_paths)
    print(f"Found {total} images in {args.dataset}")
    print(f"Batch size: {args.batch_size}")
    print(f"GPU device: {args.gpu_device_id}")
    print(f"Database: {settings.database_url}")
    print(f"Qdrant: {settings.qdrant_url}")
    print(f"MinIO: {settings.minio_url}")

    # Build GPU pipeline once. FacePipeline reads TRT_ENGINE_DIR and MODELS_DIR
    # from settings, so make sure those env vars point at the host directories.
    pipeline = FacePipeline(settings=settings, decoder_backend=args.decoder_backend)
    print(f"FacePipeline ready (decoder_backend={args.decoder_backend})")

    # Storage / vector clients
    storage = ObjectStorage(client=get_minio_client(settings), settings=settings)
    vector_store = VectorStore(client=get_qdrant_client(settings), settings=settings)
    await storage.ensure_bucket(settings.minio_bucket_people_photos)
    await storage.ensure_bucket(settings.minio_bucket_face_crops)
    await vector_store.ensure_collection(
        settings.recognizer_model_name,
        settings.recognizer_embedding_dimension,
        settings.recognizer_version,
    )
    print("Buckets and vector collection ensured")

    engine = get_db_engine()
    person_ids: list[UUID] = []

    # Warm up the DALI pipeline and TensorRT contexts using a small dummy batch.
    # This pays the one-time build/deserialize cost before the timed loop so the
    # first real batch runs at the sustained rate instead of 10x slower.
    warmup_count = min(32, total)
    if warmup_count > 0:
        print(f"Warming up pipeline with {warmup_count} images...")
        warmup_bytes = read_image_batch(image_paths[:warmup_count])
        _ = pipeline.enroll_batch(warmup_bytes)
        print("Warmup done.")

    total_persons = 0
    total_faces = 0
    total_samples = 0
    start_time = time.perf_counter()
    inference_time = 0.0
    io_time = 0.0

    for batch_start in range(0, total, args.batch_size):
        batch_paths = image_paths[batch_start : batch_start + args.batch_size]
        batch_bytes = read_image_batch(batch_paths)

        t0 = time.perf_counter()
        outputs_per_image = pipeline.enroll_batch(batch_bytes)
        t1 = time.perf_counter()
        inference_time += t1 - t0

        # Filter by quality if requested.
        if args.min_face_quality > 0.0:
            outputs_per_image = [
                [o for o in outputs if o.quality_score >= args.min_face_quality]
                for outputs in outputs_per_image
            ]

        t2 = time.perf_counter()
        async with get_async_session_maker()() as session:
            persons, faces, samples = await persist_batch(
                session,
                storage,
                vector_store,
                person_ids,
                batch_paths,
                batch_bytes,
                outputs_per_image,
                settings,
            )
        t3 = time.perf_counter()
        io_time += t3 - t2

        total_persons += persons
        total_faces += faces
        total_samples += samples

        elapsed = time.perf_counter() - start_time
        processed = batch_start + len(batch_paths)
        img_per_sec = processed / elapsed if elapsed > 0 else 0
        print(
            f"Processed {processed}/{total} images | "
            f"persons={total_persons} faces={total_faces} samples={total_samples} | "
            f"{img_per_sec:.1f} img/s | "
            f"inference={inference_time:.1f}s io={io_time:.1f}s"
        )

    elapsed = time.perf_counter() - start_time
    print("\nDone.")
    print(f"Total images: {total}")
    print(f"Total persons: {total_persons}")
    print(f"Total faces: {total_faces}")
    print(f"Total samples: {total_samples}")
    print(f"Wall time: {elapsed:.1f}s")
    print(f"Average throughput: {total / elapsed:.1f} img/s")
    print(f"Inference time: {inference_time:.1f}s")
    print(f"I/O time: {io_time:.1f}s")

    await engine.dispose()


async def main() -> None:
    args = parse_args()

    # Force host-side paths and ports for the docker-compose services.
    # These override any .env file values because uv run loads .env first.
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://mergen:mergen@localhost:5433/mergenvision"
    os.environ["QDRANT_URL"] = "http://localhost:6334"
    os.environ["MINIO_URL"] = "localhost:9002"
    os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
    os.environ["MINIO_SECRET_KEY"] = "minioadmin"
    os.environ["MINIO_SECURE"] = "false"
    os.environ["TRT_ENGINE_DIR"] = "/home/user/MergenVision/artifacts/trt_engines"
    os.environ["MODELS_DIR"] = "/home/user/MergenVision/artifacts/model_benchmarks/models"
    os.environ["GPU_DEVICE_ID"] = str(args.gpu_device_id)

    get_settings.cache_clear()
    get_db_engine.cache_clear()
    get_async_session_maker.cache_clear()
    settings = get_settings()
    await run_enrollment(args, settings)


if __name__ == "__main__":
    asyncio.run(main())
