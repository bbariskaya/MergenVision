"""High-throughput batch enrollment with GPU inference and async bulk I/O."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.core.ids import new_uuid7
from app.domain.models import FaceIdentity, FaceSample, PersonPhoto
from app.infrastructure.adapters.base import EnrollBatchResult, EnrollOutput
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import ObjectStorage, UploadItem
from app.infrastructure.vector_store import VectorStore, collection_name
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository

if TYPE_CHECKING:
    from app.infrastructure.adapters.base import ImageValidationResult


class BatchEnrollmentPipeline:
    """Enroll many photos for one person using packed batch inference.

    Responsibilities:

    - Run ``FacePipeline.enroll_batch`` in a thread pool.
    - Create ``face_identity`` rows in bulk.
    - Upload original images and face crops concurrently.
    - Insert ``person_photo`` and ``face_sample`` rows with bulk inserts.
    - Upsert embeddings into Qdrant in chunked batches.

    Inference is completed before persistence begins so that all heavy GPU work
    is done before the async I/O lane starts, but all I/O operations within the
    persistence phase run concurrently wherever possible.
    """

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
        self._face_pipeline = face_pipeline or FacePipeline(settings=self._settings)
        self._person_repo = person_repo
        self._photo_repo = photo_repo
        self._identity_repo = identity_repo
        self._sample_repo = sample_repo
        self._storage = storage
        self._vector_store = vector_store

    async def enroll_batch(
        self,
        person_id: UUID,
        image_bytes_iterable: Iterable[bytes],
    ) -> EnrollBatchResult:
        if self._person_repo is None or self._photo_repo is None:
            raise RuntimeError("BatchEnrollmentPipeline is not fully wired")

        person = await self._person_repo.get_by_id(person_id)
        if person is None:
            raise NotFoundError("Person not found")

        image_bytes = list(image_bytes_iterable)
        if not image_bytes:
            return EnrollBatchResult(
                person_id=person_id,
                photo_count=0,
                face_count=0,
                sample_count=0,
                photo_ids=[],
                face_ids=[],
                sample_ids=[],
            )

        validations = self._validate_all(image_bytes)

        loop = asyncio.get_running_loop()
        outputs_per_image = await loop.run_in_executor(
            None, self._face_pipeline.enroll_batch, image_bytes
        )

        indexed_outputs: list[tuple[int, EnrollOutput]] = []
        for img_idx, outputs in enumerate(outputs_per_image):
            for output in outputs:
                indexed_outputs.append((img_idx, output))

        display_name = " ".join(filter(None, [person.firstName, person.lastName])) or None

        # Create one face identity per detected face.
        identities: list[FaceIdentity] = []
        if indexed_outputs:
            identities = await self._identity_repo.bulk_create_known(
                [
                    FaceIdentity(
                        identityType="known",
                        personId=person_id,
                        displayName=display_name,
                    )
                    for _ in indexed_outputs
                ]
            )

        photos, original_uploads = self._prepare_photos(person_id, image_bytes, validations)
        await self._storage.upload_concurrent(original_uploads)
        photos = await self._photo_repo.bulk_create(photos)

        samples, crop_uploads, points = self._prepare_samples(identities, photos, indexed_outputs)
        if crop_uploads:
            await self._storage.upload_concurrent(crop_uploads)
        if samples:
            samples = await self._sample_repo.bulk_create(samples)

        if points:
            await self._vector_store.upsert_batch(points, batch_size=500)

        return EnrollBatchResult(
            person_id=person_id,
            photo_count=len(photos),
            face_count=len(identities),
            sample_count=len(samples),
            photo_ids=[p.photoId for p in photos],
            face_ids=[i.faceId for i in identities],
            sample_ids=[s.sampleId for s in samples],
        )

    def _validate_all(
        self,
        image_bytes: list[bytes],
    ) -> list[ImageValidationResult]:
        return [self._face_pipeline.validate(data) for data in image_bytes]

    def _prepare_photos(
        self,
        person_id: UUID,
        image_bytes: list[bytes],
        validations: list[ImageValidationResult],
    ) -> tuple[list[PersonPhoto], list[UploadItem]]:
        photos: list[PersonPhoto] = []
        uploads: list[UploadItem] = []
        for data, validation in zip(image_bytes, validations, strict=True):
            photo_id = new_uuid7()
            key = f"{person_id}/{photo_id}.jpg"
            photos.append(
                PersonPhoto(
                    photoId=photo_id,
                    personId=person_id,
                    originalImageBucket=self._settings.minio_bucket_people_photos,
                    originalImageKey=key,
                    contentType=validation.content_type,
                    sizeBytes=len(data),
                    width=validation.width,
                    height=validation.height,
                )
            )
            uploads.append(
                UploadItem(
                    bucket=self._settings.minio_bucket_people_photos,
                    key=key,
                    data=data,
                    content_type=validation.content_type,
                )
            )
        return photos, uploads

    def _prepare_samples(
        self,
        identities: list[FaceIdentity],
        photos: list[PersonPhoto],
        indexed_outputs: list[tuple[int, EnrollOutput]],
    ) -> tuple[list[FaceSample], list[UploadItem], list[dict]]:
        samples: list[FaceSample] = []
        uploads: list[UploadItem] = []
        points: list[dict] = []

        for identity, (img_idx, output) in zip(identities, indexed_outputs, strict=True):
            photo = photos[img_idx]
            sample_id = new_uuid7()
            qdrant_point_id = new_uuid7()
            crop_key = f"{identity.faceId}/{sample_id}.jpg"
            collection = collection_name(
                output.model_name,
                output.dimension,
                output.model_version,
                prefix=self._settings.qdrant_collection_prefix,
            )

            samples.append(
                FaceSample(
                    sampleId=sample_id,
                    faceId=identity.faceId,
                    photoId=photo.photoId,
                    qdrantPointId=qdrant_point_id,
                    collectionName=collection,
                    modelName=output.model_name,
                    modelVersion=output.model_version,
                    embeddingDimension=output.dimension,
                    qualityScore=output.quality_score,
                    cropImageBucket=self._settings.minio_bucket_face_crops,
                    cropImageKey=crop_key,
                    isIndexed=True,
                )
            )
            uploads.append(
                UploadItem(
                    bucket=self._settings.minio_bucket_face_crops,
                    key=crop_key,
                    data=output.crop_bytes,
                    content_type="image/jpeg",
                )
            )
            points.append(
                {
                    "id": qdrant_point_id,
                    "vector": output.embedding,
                    "payload": {
                        "faceId": str(identity.faceId),
                        "personId": str(identity.personId),
                        "photoId": str(photo.photoId),
                        "sampleId": str(sample_id),
                        "identityType": identity.identityType,
                        "modelName": output.model_name,
                        "modelVersion": output.model_version,
                        "embeddingDimension": output.dimension,
                        "isActive": True,
                    },
                }
            )

        return samples, uploads, points
