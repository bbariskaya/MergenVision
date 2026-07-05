"""Photo application service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.domain.models import PersonPhoto
from app.infrastructure.storage import ObjectStorage, get_object_storage
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.photo_repo import PhotoRepository


class PhotoService:
    """Business operations for person photos and derived face samples."""

    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repo = PhotoRepository(session)
        self._sample_repo = FaceSampleRepository(session)
        self._storage = storage or get_object_storage()
        self._settings = settings or get_settings()

    async def list_by_person(
        self,
        person_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[PersonPhoto], int]:
        return await self._repo.list_active_by_person(person_id, limit=limit, offset=offset)

    async def delete(self, person_id: UUID, photo_id: UUID) -> bool:
        photo = await self._repo.get_by_id(photo_id)
        if photo is None or photo.personId != person_id:
            raise NotFoundError("Photo not found")
        # Soft-delete the photo and its face samples.
        await self._sample_repo.soft_delete_by_photo(photo_id)
        return await self._repo.soft_delete(photo_id)

    async def get_image_url(self, photo: PersonPhoto) -> str:
        return await self._storage.presigned_get_url(
            bucket=photo.originalImageBucket,
            key=photo.originalImageKey,
            expires=self._settings.minio_url_expiry_seconds,
        )

    async def get_crop_url(self, crop_bucket: str | None, crop_key: str | None) -> str | None:
        if crop_bucket is None or crop_key is None:
            return None
        return await self._storage.presigned_get_url(
            bucket=crop_bucket,
            key=crop_key,
            expires=self._settings.minio_url_expiry_seconds,
        )
