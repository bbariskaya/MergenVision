"""Unit tests for BatchEnrollmentPipeline."""

from __future__ import annotations

from collections.abc import Iterable
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import numpy as np
import pytest

from app.core.errors import NotFoundError
from app.domain.models import Person
from app.infrastructure.adapters.base import EnrollBatchResult, EnrollOutput
from app.infrastructure.adapters.batch_enrollment_pipeline import BatchEnrollmentPipeline
from app.infrastructure.storage import UploadItem
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository


def _make_enroll_output(embedding: list[float] | None = None) -> EnrollOutput:
    return EnrollOutput(
        crop_bytes=b"crop",
        embedding=np.array(embedding or [0.1] * 512, dtype=np.float32),
        bbox=(0.0, 0.0, 1.0, 1.0),
        landmarks=[(0.0, 0.0), (1.0, 0.0), (0.5, 0.5), (0.0, 1.0), (1.0, 1.0)],
        quality_score=0.95,
        model_name="arcface",
        model_version="batch",
        dimension=512,
    )


def _make_person() -> Person:
    person = MagicMock(spec=Person)
    person.personId = uuid4()
    person.firstName = "Barış"
    person.lastName = "Özcan"
    return person


def _make_pipeline(
    outputs: list[list[EnrollOutput]] | None = None,
) -> BatchEnrollmentPipeline:
    settings = MagicMock()
    settings.minio_bucket_people_photos = "people-photos"
    settings.minio_bucket_face_crops = "face-crops"
    settings.qdrant_collection_prefix = "face_samples"

    face_pipeline = MagicMock()
    face_pipeline.validate.return_value = MagicMock(
        content_type="image/jpeg", width=100, height=100
    )
    face_pipeline.enroll_batch.return_value = outputs or []

    person_repo = MagicMock(spec=PersonRepository)
    person_repo.get_by_id = AsyncMock(return_value=_make_person())

    photo_repo = MagicMock(spec=PhotoRepository)
    photo_repo.bulk_create = AsyncMock(side_effect=lambda photos: photos)

    identity_repo = MagicMock(spec=FaceIdentityRepository)
    identity_repo.bulk_create_known = AsyncMock(side_effect=lambda identities: identities)

    sample_repo = MagicMock(spec=FaceSampleRepository)
    sample_repo.bulk_create = AsyncMock(side_effect=lambda samples: samples)

    storage = MagicMock()
    storage.upload_concurrent = AsyncMock(return_value=[])

    vector_store = MagicMock()
    vector_store.upsert_batch = AsyncMock(return_value=None)

    return BatchEnrollmentPipeline(
        face_pipeline=face_pipeline,
        person_repo=person_repo,
        photo_repo=photo_repo,
        identity_repo=identity_repo,
        sample_repo=sample_repo,
        storage=storage,
        vector_store=vector_store,
        settings=settings,
    )


@pytest.mark.asyncio
async def test_enroll_batch_empty_iterable() -> None:
    """An empty iterable returns a zero-count result."""
    pipeline = _make_pipeline()
    person_id = uuid4()

    result = await pipeline.enroll_batch(person_id, [])

    assert result == EnrollBatchResult(
        person_id=person_id,
        photo_count=0,
        face_count=0,
        sample_count=0,
        photo_ids=[],
        face_ids=[],
        sample_ids=[],
    )
    pipeline._face_pipeline.enroll_batch.assert_not_called()


@pytest.mark.asyncio
async def test_enroll_batch_person_not_found() -> None:
    """Missing person raises NotFoundError."""
    pipeline = _make_pipeline()
    pipeline._person_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError, match="Person not found"):
        await pipeline.enroll_batch(uuid4(), [b"image"])


@pytest.mark.asyncio
async def test_enroll_batch_requires_repos() -> None:
    """Unwired pipeline raises RuntimeError."""
    pipeline = BatchEnrollmentPipeline(settings=MagicMock())

    with pytest.raises(RuntimeError, match="not fully wired"):
        await pipeline.enroll_batch(uuid4(), [b"image"])


@pytest.mark.asyncio
async def test_enroll_batch_persists_all_lanes() -> None:
    """Successful batch runs inference and persists via all bulk/async paths."""
    outputs = [[_make_enroll_output()], [_make_enroll_output()]]
    pipeline = _make_pipeline(outputs=outputs)

    result = await pipeline.enroll_batch(uuid4(), [b"img1", b"img2"])

    assert result.photo_count == 2
    assert result.face_count == 2
    assert result.sample_count == 2
    assert len(result.photo_ids) == 2
    assert len(result.face_ids) == 2
    assert len(result.sample_ids) == 2

    pipeline._face_pipeline.enroll_batch.assert_called_once()
    pipeline._photo_repo.bulk_create.assert_awaited_once()
    pipeline._identity_repo.bulk_create_known.assert_awaited_once()
    pipeline._sample_repo.bulk_create.assert_awaited_once()
    pipeline._vector_store.upsert_batch.assert_awaited_once()

    # Storage should receive both original and crop uploads.
    calls = pipeline._storage.upload_concurrent.await_args_list
    assert len(calls) == 2
    first_items: Iterable[UploadItem] = calls[0].args[0]
    second_items: Iterable[UploadItem] = calls[1].args[0]
    assert len(list(first_items)) == 2  # original images
    assert len(list(second_items)) == 2  # face crops


@pytest.mark.asyncio
async def test_enroll_batch_no_faces_still_creates_photos() -> None:
    """Photos without detected faces are persisted but produce no samples."""
    pipeline = _make_pipeline(outputs=[[], []])

    result = await pipeline.enroll_batch(uuid4(), [b"img1", b"img2"])

    assert result.photo_count == 2
    assert result.face_count == 0
    assert result.sample_count == 0
    pipeline._photo_repo.bulk_create.assert_awaited_once()
    pipeline._identity_repo.bulk_create_known.assert_not_called()
    pipeline._sample_repo.bulk_create.assert_not_called()
    pipeline._vector_store.upsert_batch.assert_not_called()
