#!/usr/bin/env python3
"""Load the LFW dataset into the MergenVision system using batch enrollment.

Creates one person per LFW identity directory and enrolls all of that identity's
images using ``BatchEnrollmentPipeline``. This keeps the heavy ML inference on
GPU and persists photos, identities, samples and embeddings in bulk.

Usage inside a backend container::

    uv run python scripts/load_lfw_to_system.py \
        --lfw-dir /home/user/MergenVision/test_datasets/lfw/lfw-deepfunneled/lfw-deepfunneled
"""

from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path
from app.application.enrollment_service import EnrollmentService
from app.core.config import get_settings
from app.core.security import hash_national_id, mask_national_id
from app.domain.models import Person
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.db import AsyncSessionLocal
from app.infrastructure.storage import get_object_storage
from app.infrastructure.vector_store import get_vector_store


def _identity_name_parts(dir_name: str) -> tuple[str, str]:
    """Convert 'First_Last' directory names into (first_name, last_name)."""
    parts = dir_name.replace("_", " ").split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


async def _load_identity(
    identity_dir: Path,
    index: int,
    offset: int,
    face_pipeline: FacePipeline,
    stats: dict[str, int],
) -> None:
    """Create a person and enroll every image in the identity directory."""
    first_name, last_name = _identity_name_parts(identity_dir.name)
    national_id = f"LFW{offset + index + 1:09d}"

    image_paths = sorted(identity_dir.glob("*.jpg"))
    if not image_paths:
        return

    image_bytes = [path.read_bytes() for path in image_paths]

    async with AsyncSessionLocal() as session:
        person = Person(
            firstName=first_name,
            lastName=last_name,
            nationalIdHash=hash_national_id(national_id),
            nationalIdMasked=mask_national_id(national_id),
            details={"source": "lfw"},
        )
        session.add(person)
        await session.flush()

        settings = get_settings()
        service = EnrollmentService(
            session=session,
            face_pipeline=face_pipeline,
            storage=get_object_storage(settings=settings),
            vector_store=get_vector_store(settings=settings),
            settings=settings,
        )
        result = await service.enroll_photos_batch(
            person_id=person.personId,
            image_bytes_iterable=image_bytes,
        )
        await session.commit()

    stats["identities"] += 1
    stats["photos"] += result.photo_count
    stats["faces"] += result.face_count


async def main() -> None:
    parser = argparse.ArgumentParser(description="Load LFW into MergenVision")
    parser.add_argument(
        "--lfw-dir",
        type=Path,
        default=Path("/home/user/MergenVision/test_datasets/lfw/lfw-deepfunneled/lfw-deepfunneled"),
        help="Directory containing LFW identity subdirectories",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N identities (after offset)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N identity directories",
    )
    args = parser.parse_args()

    all_identity_dirs = sorted(
        [path for path in args.lfw_dir.iterdir() if path.is_dir()]
    )
    identity_dirs = all_identity_dirs[args.offset :]
    if args.limit:
        identity_dirs = identity_dirs[: args.limit]
    total_identities = len(all_identity_dirs)

    settings = get_settings()
    face_pipeline = FacePipeline(settings=settings)
    storage = get_object_storage(settings=settings)
    vector_store = get_vector_store(settings=settings)

    # Ensure the vector store collection is ready before bulk upserts.
    await vector_store.ensure_collection(
        settings.recognizer_model_name,
        settings.recognizer_embedding_dimension,
        settings.recognizer_version,
    )

    stats: dict[str, int] = {"identities": 0, "photos": 0, "faces": 0, "errors": 0}
    start = time.perf_counter()

    for index, identity_dir in enumerate(identity_dirs):
        try:
            await _load_identity(
                identity_dir,
                index,
                args.offset,
                face_pipeline,
                stats,
            )
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            print(f"[ERROR] {identity_dir.name}: {exc}")

        processed = args.offset + index + 1
        if (index + 1) % 100 == 0 or index + 1 == len(identity_dirs):
            elapsed = time.perf_counter() - start
            print(
                f"[PROGRESS] {processed}/{total_identities} identities | "
                f"photos={stats['photos']} faces={stats['faces']} errors={stats['errors']} | "
                f"elapsed={elapsed:.1f}s"
            )

    total = time.perf_counter() - start
    print("\n=== LFW Load Complete ===")
    print(f"identities : {stats['identities']}")
    print(f"photos     : {stats['photos']}")
    print(f"faces      : {stats['faces']}")
    print(f"errors     : {stats['errors']}")
    print(f"total_seconds: {total:.3f}")
    if stats["photos"]:
        print(f"img/s      : {stats['photos'] / total:.1f}")


if __name__ == "__main__":
    asyncio.run(main())
