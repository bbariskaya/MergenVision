"""Unit tests for EnrollmentService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.application.enrollment_service import EnrollmentService, EnrollResult
from app.core.errors import NotFoundError, ValidationError
from app.domain.models import FaceIdentity, FaceSample, Person, PersonPhoto
from app.infrastructure.adapters.base import EnrollBatchResult


def _make_person() -> Person:
    person = MagicMock(spec=Person)
    person.personId = uuid4()
    person.firstName = "Barış"
    person.lastName = "Özcan"
    return person


def _make_photo() -> PersonPhoto:
    photo = MagicMock(spec=PersonPhoto)
    photo.photoId = uuid4()
    photo.originalImageBucket = "people-photos"
    photo.originalImageKey = f"{uuid4()}/photo.jpg"
    return photo


def _make_identity() -> FaceIdentity:
    identity = MagicMock(spec=FaceIdentity)
    identity.faceId = uuid4()
    identity.identityType = "known"
    identity.personId = uuid4()
    return identity


def _make_sample() -> FaceSample:
    sample = MagicMock(spec=FaceSample)
    sample.sampleId = uuid4()
    sample.qdrantPointId = uuid4()
    sample.modelName = "arcface_w600k_r50_batch"
    sample.modelVersion = "batch"
    sample.embeddingDimension = 512
    sample.isIndexed = True
    sample.cropImageBucket = "face-crops"
    sample.cropImageKey = f"{uuid4()}/crop.jpg"
    sample.qualityScore = 0.94
    return sample


def _make_batch_result(person_id: UUID) -> EnrollBatchResult:
    return EnrollBatchResult(
        person_id=person_id,
        photo_count=2,
        face_count=2,
        sample_count=2,
        photo_ids=[uuid4(), uuid4()],
        face_ids=[uuid4(), uuid4()],
        sample_ids=[uuid4(), uuid4()],
    )


@pytest.fixture
def service():
    svc = EnrollmentService(
        session=MagicMock(),
        face_pipeline=MagicMock(),
        storage=MagicMock(),
        vector_store=MagicMock(),
        settings=MagicMock(),
    )
    svc._pipeline = MagicMock()
    svc._audit = MagicMock()
    return svc


@pytest.mark.asyncio
async def test_enroll_photo_returns_enroll_result(service):
    person = _make_person()
    photo = _make_photo()
    identity = _make_identity()
    sample = _make_sample()
    service._pipeline.enroll = AsyncMock(return_value=(person, photo, identity, sample))
    service._audit.log = AsyncMock(return_value=MagicMock())

    image_bytes = b"fake-image"
    result = await service.enroll_photo(person.personId, image_bytes)

    assert isinstance(result, EnrollResult)
    assert result.person is person
    assert result.photo is photo
    assert result.identity is identity
    assert result.sample is sample
    service._pipeline.enroll.assert_awaited_once_with(
        image_bytes=image_bytes,
        person_id=person.personId,
    )
    service._audit.log.assert_awaited_once()
    call_kwargs = service._audit.log.call_args.kwargs
    assert call_kwargs["action"] == "person.enroll"
    assert call_kwargs["entity_type"] == "person"
    assert call_kwargs["entity_id"] == person.personId
    assert call_kwargs["safe_metadata"]["photoId"] == str(photo.photoId)
    assert call_kwargs["safe_metadata"]["faceId"] == str(identity.faceId)
    assert call_kwargs["safe_metadata"]["sampleId"] == str(sample.sampleId)
    assert call_kwargs["safe_metadata"]["modelName"] == sample.modelName
    assert "nationalId" not in call_kwargs["safe_metadata"]
    assert "embedding" not in call_kwargs["safe_metadata"]


@pytest.mark.asyncio
async def test_enroll_legacy_wrapper_delegates_to_enroll_photo(service):
    person = _make_person()
    photo = _make_photo()
    identity = _make_identity()
    sample = _make_sample()
    service._pipeline.enroll = AsyncMock(return_value=(person, photo, identity, sample))
    service._audit.log = AsyncMock(return_value=MagicMock())

    result = await service.enroll(image_bytes=b"fake-image", person_id=person.personId)

    assert result == (person, photo, identity, sample)
    service._pipeline.enroll.assert_awaited_once_with(
        image_bytes=b"fake-image",
        person_id=person.personId,
    )


@pytest.mark.asyncio
async def test_enroll_photo_propagates_validation_error(service):
    service._pipeline.enroll = AsyncMock(side_effect=ValidationError("No face detected"))
    service._audit.log = AsyncMock()

    with pytest.raises(ValidationError, match="No face detected"):
        await service.enroll_photo(uuid4(), b"fake-image")

    service._audit.log.assert_not_called()


@pytest.mark.asyncio
async def test_enroll_photo_propagates_not_found(service):
    service._pipeline.enroll = AsyncMock(side_effect=NotFoundError("Person not found"))
    service._audit.log = AsyncMock()

    with pytest.raises(NotFoundError, match="Person not found"):
        await service.enroll_photo(uuid4(), b"fake-image")

    service._audit.log.assert_not_called()


@pytest.mark.asyncio
async def test_enroll_photos_batch_delegates_and_audits(service):
    person_id = uuid4()
    batch_result = _make_batch_result(person_id)
    service._batch_pipeline.enroll_batch = AsyncMock(return_value=batch_result)
    service._audit.log = AsyncMock(return_value=MagicMock())

    result = await service.enroll_photos_batch(person_id, [b"img1", b"img2"])

    assert result is batch_result
    service._batch_pipeline.enroll_batch.assert_awaited_once_with(
        person_id=person_id,
        image_bytes_iterable=[b"img1", b"img2"],
    )
    service._audit.log.assert_awaited_once()
    call_kwargs = service._audit.log.call_args.kwargs
    assert call_kwargs["action"] == "person.enroll.batch"
    assert call_kwargs["entity_type"] == "person"
    assert call_kwargs["entity_id"] == person_id
    assert call_kwargs["safe_metadata"]["photoCount"] == 2
    assert call_kwargs["safe_metadata"]["faceCount"] == 2
    assert call_kwargs["safe_metadata"]["sampleCount"] == 2
    assert len(call_kwargs["safe_metadata"]["photoIds"]) == 2


@pytest.mark.asyncio
async def test_enroll_photos_batch_requires_person_id(service):
    service._batch_pipeline.enroll_batch = AsyncMock()
    service._audit.log = AsyncMock()

    with pytest.raises(ValueError, match="person_id is required"):
        await service.enroll_photos_batch(None, [b"img1"])  # type: ignore[arg-type]

    service._batch_pipeline.enroll_batch.assert_not_called()
    service._audit.log.assert_not_called()
