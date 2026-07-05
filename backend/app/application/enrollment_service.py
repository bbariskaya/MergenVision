"""Enrollment application service."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.enrollment_pipeline import EnrollmentPipeline
from app.core.config import Settings, get_settings
from app.domain.models import FaceIdentity, FaceSample, Person, PersonPhoto
from app.infrastructure.adapters.base import EnrollBatchResult
from app.infrastructure.adapters.batch_enrollment_pipeline import BatchEnrollmentPipeline
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import ObjectStorage, get_object_storage
from app.infrastructure.vector_store import VectorStore, get_vector_store
from app.repositories.audit_repo import AuditRepository
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository


@dataclass
class EnrollResult:
    """Result of successfully enrolling a photo for an existing person."""

    person: Person
    photo: PersonPhoto
    identity: FaceIdentity
    sample: FaceSample


class EnrollmentService:
    """Service wrapper around ``EnrollmentPipeline``."""

    def __init__(
        self,
        session: AsyncSession,
        face_pipeline: FacePipeline | None = None,
        storage: ObjectStorage | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._pipeline = EnrollmentPipeline(
            face_pipeline=face_pipeline or FacePipeline(settings=self._settings),
            person_repo=PersonRepository(session),
            photo_repo=PhotoRepository(session),
            identity_repo=FaceIdentityRepository(session),
            sample_repo=FaceSampleRepository(session),
            storage=storage or get_object_storage(settings=self._settings),
            vector_store=vector_store or get_vector_store(settings=self._settings),
            settings=self._settings,
        )
        self._batch_pipeline = BatchEnrollmentPipeline(
            face_pipeline=face_pipeline or FacePipeline(settings=self._settings),
            person_repo=PersonRepository(session),
            photo_repo=PhotoRepository(session),
            identity_repo=FaceIdentityRepository(session),
            sample_repo=FaceSampleRepository(session),
            storage=storage or get_object_storage(settings=self._settings),
            vector_store=vector_store or get_vector_store(settings=self._settings),
            settings=self._settings,
        )
        self._audit = AuditRepository(session)

    async def enroll_photo(
        self,
        person_id: UUID,
        image_bytes: bytes,
    ) -> EnrollResult:
        """Enroll a single photo for an existing person.

        Validates the image, detects a single face, persists the photo/sample,
        uploads original/crop bytes to object storage, upserts the embedding
        into the vector store, and writes an audit entry.
        """
        if person_id is None:
            raise ValueError("person_id is required for photo enrollment")

        person, photo, identity, sample = await self._pipeline.enroll(
            image_bytes=image_bytes,
            person_id=person_id,
        )
        await self._audit.log(
            action="person.enroll",
            entity_type="person",
            entity_id=person.personId,
            actor=None,
            request_id=None,
            outcome="success",
            safe_metadata={
                "photoId": str(photo.photoId),
                "faceId": str(identity.faceId),
                "sampleId": str(sample.sampleId),
                "modelName": sample.modelName,
                "modelVersion": sample.modelVersion,
            },
        )
        return EnrollResult(
            person=person,
            photo=photo,
            identity=identity,
            sample=sample,
        )

    async def enroll_photos_batch(
        self,
        person_id: UUID,
        image_bytes_iterable: Iterable[bytes],
    ) -> EnrollBatchResult:
        """Enroll many photos for an existing person using packed batch inference.

        Runs ML inference in a thread pool, then persists photos, identities,
        samples and vector embeddings using bulk/async operations.
        """
        if person_id is None:
            raise ValueError("person_id is required for batch enrollment")

        result = await self._batch_pipeline.enroll_batch(
            person_id=person_id,
            image_bytes_iterable=image_bytes_iterable,
        )
        await self._audit.log(
            action="person.enroll.batch",
            entity_type="person",
            entity_id=result.person_id,
            actor=None,
            request_id=None,
            outcome="success",
            safe_metadata={
                "photoCount": result.photo_count,
                "faceCount": result.face_count,
                "sampleCount": result.sample_count,
                "photoIds": [str(pid) for pid in result.photo_ids],
            },
        )
        return result

    async def enroll(
        self,
        image_bytes: bytes,
        person_id: UUID | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        national_id: str | None = None,
        details: dict | None = None,
    ) -> tuple[Person, PersonPhoto, FaceIdentity, FaceSample]:
        """Legacy wrapper kept for route compatibility.

        Phase 1 routes always supply an existing ``person_id``.
        """
        del first_name, last_name, national_id, details
        if person_id is None:
            raise NotImplementedError(
                "Creating a new person during enrollment is not supported in Phase 1"
            )
        result = await self.enroll_photo(person_id, image_bytes)
        return result.person, result.photo, result.identity, result.sample
