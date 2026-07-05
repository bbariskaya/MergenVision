"""Face sample repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid7
from app.domain.models import FaceIdentity, FaceSample


class FaceSampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        face_id: UUID,
        photo_id: UUID | None,
        qdrant_point_id: UUID,
        collection_name: str,
        model_name: str,
        model_version: str,
        embedding_dimension: int,
        quality_score: float | None = None,
        crop_bucket: str | None = None,
        crop_key: str | None = None,
    ) -> FaceSample:
        sample = FaceSample(
            faceId=face_id,
            photoId=photo_id,
            qdrantPointId=qdrant_point_id,
            collectionName=collection_name,
            modelName=model_name,
            modelVersion=model_version,
            embeddingDimension=embedding_dimension,
            qualityScore=quality_score,
            cropImageBucket=crop_bucket,
            cropImageKey=crop_key,
            isIndexed=False,
        )
        self._session.add(sample)
        await self._session.flush()
        return sample

    async def bulk_create(
        self,
        samples: list[FaceSample],
        chunk_size: int = 1000,
    ) -> list[FaceSample]:
        if not samples:
            return []
        table = FaceSample.__table__
        for sample in samples:
            if sample.sampleId is None:
                sample.sampleId = new_uuid7()
            if sample.qdrantPointId is None:
                sample.qdrantPointId = new_uuid7()
            if sample.isIndexed is None:
                sample.isIndexed = False
            if sample.isActive is None:
                sample.isActive = True
        now = datetime.now(UTC)

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i : i + chunk_size]
            values = []
            for sample in chunk:
                row = {col.key: getattr(sample, col.key) for col in table.columns}
                if row.get("createdAt") is None:
                    row["createdAt"] = now
                if row.get("updatedAt") is None:
                    row["updatedAt"] = now
                values.append(row)
            await self._session.execute(insert(table).values(values))

        return samples

    async def get_by_id(self, sample_id: UUID) -> FaceSample | None:
        stmt = select(FaceSample).where(
            FaceSample.sampleId == sample_id,
            FaceSample.isActive.is_(True),
        )
        return await self._session.scalar(stmt)

    async def mark_indexed(self, sample_id: UUID) -> bool:
        sample = await self.get_by_id(sample_id)
        if sample is None:
            return False
        sample.isIndexed = True
        sample.updatedAt = datetime.now(UTC)
        await self._session.flush()
        return True

    async def list_active_by_person(
        self,
        person_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FaceSample], int]:
        # Join through face_identity to filter by personId.
        stmt = (
            select(FaceSample)
            .join(FaceIdentity)
            .where(
                FaceIdentity.personId == person_id,
                FaceSample.isActive.is_(True),
            )
            .order_by(FaceSample.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(FaceSample)
            .join(FaceIdentity)
            .where(
                FaceIdentity.personId == person_id,
                FaceSample.isActive.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)

    async def soft_delete_by_photo(self, photo_id: UUID) -> int:
        stmt = select(FaceSample).where(
            FaceSample.photoId == photo_id,
            FaceSample.isActive.is_(True),
        )
        result = await self._session.execute(stmt)
        samples = result.scalars().all()
        for sample in samples:
            sample.isActive = False
            sample.deletedAt = datetime.now(UTC)
        await self._session.flush()
        return len(samples)

    async def soft_delete_by_person(self, person_id: UUID) -> int:
        # Join through face_identity because FaceSample has no personId column.
        stmt = (
            select(FaceSample)
            .join(FaceIdentity)
            .where(
                FaceIdentity.personId == person_id,
                FaceSample.isActive.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        samples = result.scalars().all()
        for sample in samples:
            sample.isActive = False
            sample.deletedAt = datetime.now(UTC)
        await self._session.flush()
        return len(samples)

    async def get_crop_info_by_sample_ids(
        self,
        sample_ids: list[UUID],
    ) -> dict[UUID, tuple[str | None, str | None]]:
        """Return crop image bucket/key pairs for the given sample IDs."""
        if not sample_ids:
            return {}
        stmt = select(
            FaceSample.sampleId,
            FaceSample.cropImageBucket,
            FaceSample.cropImageKey,
        ).where(
            FaceSample.sampleId.in_(sample_ids),
            FaceSample.isActive.is_(True),
        )
        result = await self._session.execute(stmt)
        return {
            row.sampleId: (row.cropImageBucket, row.cropImageKey)
            for row in result.mappings().all()
        }
