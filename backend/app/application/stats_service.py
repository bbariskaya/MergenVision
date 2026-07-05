"""Stats aggregation service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    FaceSample,
    IdentificationRequest,
    Person,
    PersonPhoto,
)


class StatsService:
    """Return high-level entity counts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summary(self) -> dict[str, int]:
        person_count = await self._count(Person)
        photo_count = await self._count(PersonPhoto)
        sample_count = await self._count(FaceSample)
        request_count = await self._count(IdentificationRequest)
        return {
            "personCount": person_count,
            "photoCount": photo_count,
            "faceSampleCount": sample_count,
            "identificationRequestCount": request_count,
        }

    async def get(self) -> dict[str, int]:
        """Backward-compatible alias for ``summary``."""
        return await self.summary()

    async def _count(self, model: type) -> int:
        stmt = select(func.count()).select_from(model)
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)
