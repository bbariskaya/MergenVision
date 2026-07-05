"""Person photo repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid7
from app.domain.models import PersonPhoto


class PhotoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        person_id: UUID,
        bucket: str,
        key: str,
        content_type: str,
        size_bytes: int,
        width: int | None,
        height: int | None,
    ) -> PersonPhoto:
        photo = PersonPhoto(
            personId=person_id,
            originalImageBucket=bucket,
            originalImageKey=key,
            contentType=content_type,
            sizeBytes=size_bytes,
            width=width,
            height=height,
        )
        self._session.add(photo)
        await self._session.flush()
        return photo

    async def bulk_create(self, photos: list[PersonPhoto]) -> list[PersonPhoto]:
        if not photos:
            return []
        table = PersonPhoto.__table__
        for photo in photos:
            if photo.photoId is None:
                photo.photoId = new_uuid7()
            if photo.isActive is None:
                photo.isActive = True
        now = datetime.now(UTC)
        values = []
        for photo in photos:
            row = {col.key: getattr(photo, col.key) for col in table.columns}
            if row.get("createdAt") is None:
                row["createdAt"] = now
            if row.get("updatedAt") is None:
                row["updatedAt"] = now
            values.append(row)
        await self._session.execute(insert(table).values(values))
        return photos

    async def get_by_id(self, photo_id: UUID) -> PersonPhoto | None:
        stmt = select(PersonPhoto).where(
            PersonPhoto.photoId == photo_id,
            PersonPhoto.isActive.is_(True),
        )
        return await self._session.scalar(stmt)

    async def list_active_by_person(
        self, person_id: UUID, limit: int, offset: int
    ) -> tuple[list[PersonPhoto], int]:
        where = (PersonPhoto.personId == person_id) & PersonPhoto.isActive.is_(True)
        stmt = (
            select(PersonPhoto)
            .where(where)
            .order_by(PersonPhoto.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(PersonPhoto).where(where)
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)

    async def soft_delete(self, photo_id: UUID) -> bool:
        photo = await self.get_by_id(photo_id)
        if photo is None:
            return False
        photo.isActive = False
        photo.deletedAt = datetime.now(UTC)
        await self._session.flush()
        return True

    async def soft_delete_by_person(self, person_id: UUID) -> int:
        stmt = select(PersonPhoto).where(
            PersonPhoto.personId == person_id,
            PersonPhoto.isActive.is_(True),
        )
        result = await self._session.execute(stmt)
        photos = result.scalars().all()
        for photo in photos:
            photo.isActive = False
            photo.deletedAt = datetime.now(UTC)
        await self._session.flush()
        return len(photos)
