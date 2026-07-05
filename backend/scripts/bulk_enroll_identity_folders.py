#!/usr/bin/env python3
"""Bulk-enroll a face dataset where each subdirectory is one identity.

Useful for Kaggle datasets such as VGGFace2 and CASIA-WebFace.
Runs outside Docker, talks to the PostgreSQL/Qdrant/MinIO services exposed by
``docker-compose.yml`` on localhost ports.

Example::

    cd backend
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/bulk_enroll_identity_folders.py \
        --dataset /home/user/MergenVision/testdatasets/vggface2 \
        --batch-size 1024 \
        --gpu-device-id 0

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
import os
import sys
import time
from pathlib import Path
from uuid import UUID

# Make ``app.*`` and sibling scripts importable.
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(script_dir))

import bulk_enroll_celeba as bulk  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402
from app.core.errors import ValidationError  # noqa: E402
from app.core.ids import new_uuid7  # noqa: E402
from app.domain.models import Person  # noqa: E402
from app.infrastructure.adapters.pipelines import FacePipeline  # noqa: E402
from app.infrastructure.db import get_async_session_maker, get_db_engine  # noqa: E402
from app.infrastructure.minio_client import get_minio_client  # noqa: E402
from app.infrastructure.qdrant_client import get_qdrant_client  # noqa: E402
from app.infrastructure.storage import ObjectStorage  # noqa: E402
from app.infrastructure.vector_store import VectorStore  # noqa: E402
from app.repositories.person_repo import PersonRepository  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk-enroll identity-folder face dataset")
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Directory containing one subdirectory per identity",
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
        "--max-identities",
        type=int,
        default=0,
        help="Max identities to process (0 = all)",
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


def discover_identities(
    dataset_dir: Path, max_images: int, max_identities: int
) -> dict[str, list[Path]]:
    if not dataset_dir.is_dir():
        raise SystemExit(f"Dataset directory not found: {dataset_dir}")

    identity_dirs = sorted(p for p in dataset_dir.iterdir() if p.is_dir())
    if not identity_dirs:
        raise SystemExit(f"No identity subdirectories found in {dataset_dir}")

    if max_identities > 0:
        identity_dirs = identity_dirs[:max_identities]

    identities: dict[str, list[Path]] = {}
    total_images = 0
    for identity_dir in identity_dirs:
        images = sorted(
            f
            for f in identity_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")
        )
        if not images:
            continue
        if max_images > 0 and total_images + len(images) > max_images:
            images = images[: max_images - total_images]
        identities[identity_dir.name] = images
        total_images += len(images)
        if max_images > 0 and total_images >= max_images:
            break

    if not identities:
        raise SystemExit(f"No *.jpg/*.png images found under {dataset_dir}")

    return identities


def split_identity_name(name: str) -> tuple[str, str]:
    """Convert 'First_Last' or 'n000001' into (first_name, last_name)."""
    parts = name.replace("_", " ").split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return name, ""


async def create_all_persons(
    session_maker,
    identities: dict[str, list[Path]],
) -> dict[str, UUID]:
    """Bulk-create all persons and return identity_name -> person_id mapping."""
    persons = []
    name_order: list[str] = []
    async with session_maker() as session:
        repo = PersonRepository(session)
        for identity_name in identities:
            first, last = split_identity_name(identity_name)
            persons.append(
                Person(
                    firstName=first,
                    lastName=last,
                    details={"source": "identity_folder", "identity_name": identity_name},
                )
            )
            name_order.append(identity_name)
        await repo.bulk_create(persons)
        await session.commit()

    return {name: person.personId for name, person in zip(name_order, persons)}


async def run_enrollment(args: argparse.Namespace, settings: Settings) -> None:
    identities = discover_identities(
        args.dataset, args.max_images, args.max_identities
    )
    total_images = sum(len(v) for v in identities.values())
    total_identities = len(identities)
    print(f"Found {total_identities} identities with {total_images} images in {args.dataset}")
    print(f"Batch size: {args.batch_size}")
    print(f"GPU device: {args.gpu_device_id}")
    print(f"Database: {settings.database_url}")
    print(f"Qdrant: {settings.qdrant_url}")
    print(f"MinIO: {settings.minio_url}")

    # Build all persons upfront so every image has a stable person_id.
    session_maker = get_async_session_maker()
    identity_to_person = await create_all_persons(session_maker, identities)
    print(f"Created {len(identity_to_person)} persons")

    # Flatten images with their person_id.
    entries: list[tuple[UUID, Path]] = []
    for identity_name, paths in identities.items():
        person_id = identity_to_person[identity_name]
        for path in paths:
            entries.append((person_id, path))

    # Build GPU pipeline once.
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

    # Warm up pipeline.
    warmup_count = min(32, len(entries))
    if warmup_count > 0:
        print(f"Warming up pipeline with {warmup_count} images...")
        warmup_bytes = bulk.read_image_batch([p for _, p in entries[:warmup_count]])
        _ = pipeline.enroll_batch(warmup_bytes)
        print("Warmup done.")

    engine = get_db_engine()

    total_persons = 0
    total_faces = 0
    total_samples = 0
    skipped_images = 0
    start_time = time.perf_counter()
    inference_time = 0.0
    io_time = 0.0

    for batch_start in range(0, len(entries), args.batch_size):
        batch_entries = entries[batch_start : batch_start + args.batch_size]
        batch_person_ids = [pid for pid, _ in batch_entries]
        batch_paths = [p for _, p in batch_entries]
        batch_bytes = bulk.read_image_batch(batch_paths)

        # Pre-validate images to keep corrupted records from killing the DALI
        # pipeline. Invalid images are skipped (empty output list).
        valid_indices: list[int] = []
        valid_bytes: list[bytes] = []
        outputs_per_image: list[list[bulk.EnrollOutput]] = [[] for _ in batch_bytes]
        for i, data in enumerate(batch_bytes):
            try:
                pipeline.validate(data)
                valid_indices.append(i)
                valid_bytes.append(data)
            except (ValidationError, OSError):
                skipped_images += 1

        t0 = time.perf_counter()
        if valid_bytes:
            valid_outputs = pipeline.enroll_batch(valid_bytes)
            for vi, outputs in zip(valid_indices, valid_outputs, strict=True):
                outputs_per_image[vi] = outputs
        t1 = time.perf_counter()
        inference_time += t1 - t0

        if args.min_face_quality > 0.0:
            outputs_per_image = [
                [o for o in outputs if o.quality_score >= args.min_face_quality]
                for outputs in outputs_per_image
            ]

        t2 = time.perf_counter()
        async with session_maker() as session:
            persons_count, faces_count, samples_count = await bulk.persist_batch(
                session,
                storage,
                vector_store,
                batch_person_ids,
                batch_paths,
                batch_bytes,
                outputs_per_image,
                settings,
            )
        t3 = time.perf_counter()
        io_time += t3 - t2

        total_persons += persons_count
        total_faces += faces_count
        total_samples += samples_count

        elapsed = time.perf_counter() - start_time
        processed = batch_start + len(batch_entries)
        img_per_sec = processed / elapsed if elapsed > 0 else 0
        print(
            f"Processed {processed}/{total_images} images | "
            f"identities={total_identities} faces={total_faces} samples={total_samples} | "
            f"skipped={skipped_images} | "
            f"{img_per_sec:.1f} img/s | "
            f"inference={inference_time:.1f}s io={io_time:.1f}s"
        )

    elapsed = time.perf_counter() - start_time
    print("\nDone.")
    print(f"Total images: {total_images}")
    print(f"Total identities: {total_identities}")
    print(f"Total faces: {total_faces}")
    print(f"Total samples: {total_samples}")
    print(f"Wall time: {elapsed:.1f}s")
    print(f"Average throughput: {total_images / elapsed:.1f} img/s")
    print(f"Inference time: {inference_time:.1f}s")
    print(f"I/O time: {io_time:.1f}s")

    await engine.dispose()


async def main() -> None:
    args = parse_args()

    # Force host-side paths and ports.
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
    bulk.get_db_engine.cache_clear()
    bulk.get_async_session_maker.cache_clear()
    settings = get_settings()
    await run_enrollment(args, settings)


if __name__ == "__main__":
    asyncio.run(main())
