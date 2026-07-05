"""Reusable FastAPI dependency factories."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit_service import AuditService
from app.application.enrollment_service import EnrollmentService
from app.application.identification_service import IdentificationService
from app.application.people_service import PeopleService
from app.application.photo_service import PhotoService
from app.application.readiness_service import ReadinessService
from app.application.stats_service import StatsService
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.db import AsyncSessionLocal
from app.infrastructure.health_checks import HealthChecks
from app.infrastructure.storage import ObjectStorage, get_object_storage
from app.infrastructure.vector_store import VectorStore, get_vector_store


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and commit at request end."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_readiness_service() -> ReadinessService:
    """Build the readiness service with the configured dependency checks."""
    return ReadinessService(health_checks=HealthChecks())


def get_face_pipeline() -> FacePipeline:
    """Return the shared face ML pipeline."""
    return FacePipeline()


def get_object_storage_dep() -> ObjectStorage:
    """Dependency provider for object storage."""
    return get_object_storage()


def get_vector_store_dep() -> VectorStore:
    """Dependency provider for vector store."""
    return get_vector_store()


def get_people_service(
    session: AsyncSession = Depends(get_db),
) -> PeopleService:
    return PeopleService(session=session)


def get_photo_service(
    session: AsyncSession = Depends(get_db),
) -> PhotoService:
    return PhotoService(session=session)


def get_enrollment_service(
    session: AsyncSession = Depends(get_db),
    face_pipeline: FacePipeline = Depends(get_face_pipeline),
    storage: ObjectStorage = Depends(get_object_storage_dep),
    vector_store: VectorStore = Depends(get_vector_store_dep),
) -> EnrollmentService:
    return EnrollmentService(
        session=session,
        face_pipeline=face_pipeline,
        storage=storage,
        vector_store=vector_store,
    )


def get_identification_service(
    session: AsyncSession = Depends(get_db),
    face_pipeline: FacePipeline = Depends(get_face_pipeline),
    storage: ObjectStorage = Depends(get_object_storage_dep),
    vector_store: VectorStore = Depends(get_vector_store_dep),
) -> IdentificationService:
    return IdentificationService(
        session=session,
        face_pipeline=face_pipeline,
        storage=storage,
        vector_store=vector_store,
    )


def get_audit_service(
    session: AsyncSession = Depends(get_db),
) -> AuditService:
    return AuditService(session=session)


def get_stats_service(
    session: AsyncSession = Depends(get_db),
) -> StatsService:
    return StatsService(session=session)
