"""Unit tests for FaceSampleRepository using a fake async session."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.domain.models import FaceSample
from app.repositories.face_sample_repo import FaceSampleRepository

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def fake_session() -> MagicMock:
    """Return a mock async SQLAlchemy session."""
    session = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


class TestFaceSampleRepository:
    """FaceSampleRepository tests using a mocked session."""

    async def test_create_builds_face_sample(self, fake_session: MagicMock) -> None:
        face_id = UUID("12345678-1234-7123-8123-123456789abc")
        photo_id = UUID("abcdef12-3456-7123-8123-abcdefabcdef")
        qdrant_point_id = UUID("11111111-2222-7123-8123-444444444444")

        repo = FaceSampleRepository(fake_session)
        sample = await repo.create(
            face_id=face_id,
            photo_id=photo_id,
            qdrant_point_id=qdrant_point_id,
            collection_name="arcface-512-v1",
            model_name="ArcFace",
            model_version="r50",
            embedding_dimension=512,
        )

        assert isinstance(sample, FaceSample)
        assert sample.faceId == face_id
        assert sample.photoId == photo_id
        assert sample.qdrantPointId == qdrant_point_id
        assert sample.collectionName == "arcface-512-v1"
        assert sample.modelName == "ArcFace"
        assert sample.modelVersion == "r50"
        assert sample.embeddingDimension == 512
        assert sample.isIndexed is False
        assert sample.qualityScore is None
        assert sample.cropImageBucket is None
        assert sample.cropImageKey is None
        fake_session.add.assert_called_once_with(sample)
        fake_session.flush.assert_awaited_once()

    async def test_create_accepts_optional_fields(self, fake_session: MagicMock) -> None:
        face_id = UUID("12345678-1234-7123-8123-123456789abc")
        photo_id = UUID("abcdef12-3456-7123-8123-abcdefabcdef")
        qdrant_point_id = UUID("11111111-2222-7123-8123-444444444444")

        repo = FaceSampleRepository(fake_session)
        sample = await repo.create(
            face_id=face_id,
            photo_id=photo_id,
            qdrant_point_id=qdrant_point_id,
            collection_name="arcface-512-v1",
            model_name="ArcFace",
            model_version="r50",
            embedding_dimension=512,
            quality_score=0.92,
            crop_bucket="samples",
            crop_key="crops/face.jpg",
        )

        assert sample.qualityScore == 0.92
        assert sample.cropImageBucket == "samples"
        assert sample.cropImageKey == "crops/face.jpg"

    async def test_mark_indexed_sets_is_indexed_true(self, fake_session: MagicMock) -> None:
        sample = FaceSample(
            faceId=UUID("12345678-1234-7123-8123-123456789abc"),
            photoId=UUID("abcdef12-3456-7123-8123-abcdefabcdef"),
            qdrantPointId=UUID("11111111-2222-7123-8123-444444444444"),
            collectionName="arcface-512-v1",
            modelName="ArcFace",
            modelVersion="r50",
            embeddingDimension=512,
            isIndexed=False,
            isActive=True,
            updatedAt=datetime.now(UTC) - timedelta(minutes=5),
        )
        fake_session.scalar.return_value = sample

        repo = FaceSampleRepository(fake_session)
        result = await repo.mark_indexed(sample.sampleId)

        assert result is True
        assert sample.isIndexed is True
        fake_session.flush.assert_awaited_once()
