"""Unit tests for PhotoService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.photo_service import PhotoService
from app.core.errors import NotFoundError
from app.domain.models import PersonPhoto


def _make_photo(**kwargs) -> PersonPhoto:
    photo = MagicMock(spec=PersonPhoto)
    photo.photoId = kwargs.get("photo_id", uuid4())
    photo.personId = kwargs.get("person_id", uuid4())
    photo.originalImageBucket = kwargs.get("bucket", "people-photos")
    photo.originalImageKey = kwargs.get("key", f"{uuid4()}/photo.jpg")
    photo.contentType = kwargs.get("content_type", "image/jpeg")
    photo.sizeBytes = kwargs.get("size_bytes", 1024)
    photo.width = kwargs.get("width", 100)
    photo.height = kwargs.get("height", 100)
    photo.isActive = True
    return photo


@pytest.fixture
def service():
    svc = PhotoService(
        session=MagicMock(),
        storage=MagicMock(),
        settings=MagicMock(minio_url_expiry_seconds=3600),
    )
    svc._repo = MagicMock()
    svc._sample_repo = MagicMock()
    return svc


@pytest.mark.asyncio
async def test_list_by_person_delegates(service):
    photo = _make_photo()
    service._repo.list_active_by_person = AsyncMock(return_value=([photo], 1))

    items, total = await service.list_by_person(uuid4(), limit=20, offset=0)

    assert items == [photo]
    assert total == 1


@pytest.mark.asyncio
async def test_delete_raises_when_photo_missing(service):
    service._repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.delete(uuid4(), uuid4())

    service._repo.soft_delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_raises_when_photo_belongs_to_another_person(service):
    photo = _make_photo(person_id=uuid4())
    service._repo.get_by_id = AsyncMock(return_value=photo)

    with pytest.raises(NotFoundError):
        await service.delete(uuid4(), photo.photoId)


@pytest.mark.asyncio
async def test_delete_soft_deletes_photo_and_samples(service):
    person_id = uuid4()
    photo = _make_photo(person_id=person_id)
    service._repo.get_by_id = AsyncMock(return_value=photo)
    service._sample_repo.soft_delete_by_photo = AsyncMock()
    service._repo.soft_delete = AsyncMock(return_value=True)

    result = await service.delete(person_id, photo.photoId)

    assert result is True
    service._sample_repo.soft_delete_by_photo.assert_awaited_once_with(photo.photoId)
    service._repo.soft_delete.assert_awaited_once_with(photo.photoId)


@pytest.mark.asyncio
async def test_get_image_url_presigns_original(service):
    photo = _make_photo()
    service._storage.presigned_get_url = AsyncMock(return_value="http://example.com/original")

    url = await service.get_image_url(photo)

    assert url == "http://example.com/original"
    service._storage.presigned_get_url.assert_awaited_once_with(
        bucket=photo.originalImageBucket,
        key=photo.originalImageKey,
        expires=service._settings.minio_url_expiry_seconds,
    )


@pytest.mark.asyncio
async def test_get_crop_url_returns_none_when_missing(service):
    assert await service.get_crop_url(None, None) is None
    assert await service.get_crop_url("bucket", None) is None
    assert await service.get_crop_url(None, "key") is None


@pytest.mark.asyncio
async def test_get_crop_url_presigns_crop(service):
    service._storage.presigned_get_url = AsyncMock(return_value="http://example.com/crop")

    url = await service.get_crop_url("face-crops", "face/crop.jpg")

    assert url == "http://example.com/crop"
