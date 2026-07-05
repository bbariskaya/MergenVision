"""Enrollment orchestration: detect, embed, store, index."""

from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, ValidationError
from app.core.ids import new_uuid7
from app.domain.models import FaceIdentity, FaceSample, Person, PersonPhoto
from app.infrastructure.adapters.base import EnrollOutput, ImageValidationResult
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import ObjectStorage
from app.infrastructure.vector_store import VectorStore, collection_name
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository


class EnrollmentPipeline:
    """Enroll a person from a single photo."""

    def __init__(
        self,
        face_pipeline: FacePipeline | None = None,
        person_repo: PersonRepository | None = None,
        photo_repo: PhotoRepository | None = None,
        identity_repo: FaceIdentityRepository | None = None,
        sample_repo: FaceSampleRepository | None = None,
        storage: ObjectStorage | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._face_pipeline = face_pipeline
        self._person_repo = person_repo
        self._photo_repo = photo_repo
        self._identity_repo = identity_repo
        self._sample_repo = sample_repo
        self._storage = storage
        self._vector_store = vector_store

    async def enroll(
        self,
        image_bytes: bytes,
        person_id: UUID | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        national_id_hash: str | None = None,
        national_id_masked: str | None = None,
        details: dict | None = None,
    ) -> tuple[Person, PersonPhoto, FaceIdentity, FaceSample]:
        """Run ML inference and persist the enrolled identity.

        If ``person_id`` is provided, the face is added to the existing person.
        Otherwise a new person is created from the supplied fields.
        """
        if self._face_pipeline is None or self._person_repo is None:
            raise RuntimeError("EnrollmentPipeline is not fully wired")

        validation = self._face_pipeline.validate(image_bytes)
        outputs = await self._run_face_pipeline(image_bytes)
        if not outputs:
            raise ValidationError("No face detected in the uploaded image")
        if len(outputs) > 1:
            raise ValidationError(
                "Multiple faces detected; Phase 1 enrollment requires exactly one face"
            )

        best = outputs[0]

        if person_id is None:
            person = await self._person_repo.create(
                first_name=first_name,
                last_name=last_name,
                national_id_hash=national_id_hash,
                national_id_masked=national_id_masked,
                details=details,
            )
            display_name = " ".join(filter(None, [first_name, last_name])) or None
        else:
            person = await self._person_repo.get_by_id(person_id)
            if person is None:
                raise NotFoundError("Person not found")
            display_name = " ".join(filter(None, [person.firstName, person.lastName])) or None

        identity = await self._identity_repo.create_known(
            person_id=person.personId,
            display_name=display_name,
        )

        photo = await self._store_photo(person.personId, image_bytes, validation)
        sample = await self._store_sample(identity, photo, best)
        await self._index_sample(identity, sample, best)
        await self._sample_repo.mark_indexed(sample.sampleId)

        return person, photo, identity, sample

    async def _run_face_pipeline(self, image_bytes: bytes) -> list[EnrollOutput]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._face_pipeline.enroll, image_bytes)

    async def _store_photo(
        self,
        person_id: UUID,
        image_bytes: bytes,
        validation: ImageValidationResult,
    ) -> PersonPhoto:
        key = f"{person_id}/{new_uuid7()}.jpg"
        await self._storage.upload(
            bucket=self._settings.minio_bucket_people_photos,
            key=key,
            data=image_bytes,
            content_type=validation.content_type,
        )
        return await self._photo_repo.create(
            person_id=person_id,
            bucket=self._settings.minio_bucket_people_photos,
            key=key,
            content_type=validation.content_type,
            size_bytes=len(image_bytes),
            width=validation.width,
            height=validation.height,
        )

    async def _store_sample(
        self,
        identity: FaceIdentity,
        photo: PersonPhoto,
        output: EnrollOutput,
    ) -> FaceSample:
        crop_key = f"{identity.faceId}/{new_uuid7()}.jpg"
        await self._storage.upload(
            bucket=self._settings.minio_bucket_face_crops,
            key=crop_key,
            data=output.crop_bytes,
            content_type="image/jpeg",
        )

        qdrant_point_id = new_uuid7()
        collection = collection_name(
            output.model_name,
            output.dimension,
            output.model_version,
            prefix=self._settings.qdrant_collection_prefix,
        )
        return await self._sample_repo.create(
            face_id=identity.faceId,
            photo_id=photo.photoId,
            qdrant_point_id=qdrant_point_id,
            collection_name=collection,
            model_name=output.model_name,
            model_version=output.model_version,
            embedding_dimension=output.dimension,
            quality_score=output.quality_score,
            crop_bucket=self._settings.minio_bucket_face_crops,
            crop_key=crop_key,
        )

    async def _index_sample(
        self,
        identity: FaceIdentity,
        sample: FaceSample,
        output: EnrollOutput,
    ) -> None:
        await self._vector_store.upsert_batch(
            points=[
                {
                    "id": sample.qdrantPointId,
                    "vector": output.embedding,
                    "payload": {
                        "faceId": str(identity.faceId),
                        "personId": str(identity.personId),
                        "photoId": str(sample.photoId),
                        "sampleId": str(sample.sampleId),
                        "identityType": identity.identityType,
                        "modelName": output.model_name,
                        "modelVersion": output.model_version,
                        "embeddingDimension": output.dimension,
                        "isActive": True,
                    },
                }
            ],
        )
