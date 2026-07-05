"""Face identity repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid7
from app.domain.models import FaceIdentity


class FaceIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_known(
        self,
        person_id: UUID,
        display_name: str | None,
    ) -> FaceIdentity:
        identity = FaceIdentity(
            identityType="known",
            personId=person_id,
            displayName=display_name,
        )
        self._session.add(identity)
        await self._session.flush()
        return identity

    async def bulk_create_known(
        self,
        identities: list[FaceIdentity],
        chunk_size: int = 1000,
    ) -> list[FaceIdentity]:
        if not identities:
            return []
        table = FaceIdentity.__table__
        for identity in identities:
            if identity.faceId is None:
                identity.faceId = new_uuid7()
            if identity.identityType is None:
                identity.identityType = "known"
            if identity.isActive is None:
                identity.isActive = True
        now = datetime.now(UTC)

        for i in range(0, len(identities), chunk_size):
            chunk = identities[i : i + chunk_size]
            values = []
            for identity in chunk:
                row = {col.key: getattr(identity, col.key) for col in table.columns}
                if row.get("createdAt") is None:
                    row["createdAt"] = now
                if row.get("updatedAt") is None:
                    row["updatedAt"] = now
                values.append(row)
            await self._session.execute(insert(table).values(values))

        return identities

    async def get_by_id(self, face_id: UUID) -> FaceIdentity | None:
        stmt = select(FaceIdentity).where(
            FaceIdentity.faceId == face_id,
            FaceIdentity.isActive.is_(True),
        )
        return await self._session.scalar(stmt)

    async def list_active_by_person(
        self,
        person_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FaceIdentity], int]:
        where = (FaceIdentity.personId == person_id) & FaceIdentity.isActive.is_(True)
        stmt = select(FaceIdentity).where(where).offset(offset).limit(limit)
        count_stmt = select(func.count()).select_from(FaceIdentity).where(where)
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)

    async def soft_delete(self, face_id: UUID) -> bool:
        identity = await self.get_by_id(face_id)
        if identity is None:
            return False
        identity.isActive = False
        identity.updatedAt = datetime.now(UTC)
        await self._session.flush()
        return True

    async def soft_delete_by_person(self, person_id: UUID) -> int:
        stmt = select(FaceIdentity).where(
            FaceIdentity.personId == person_id,
            FaceIdentity.isActive.is_(True),
        )
        result = await self._session.execute(stmt)
        identities = result.scalars().all()
        for identity in identities:
            identity.isActive = False
            identity.updatedAt = datetime.now(UTC)
        await self._session.flush()
        return len(identities)
