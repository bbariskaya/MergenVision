"""Photo and enrollment endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_photo_service
from app.application.enrollment_service import EnrollmentService
from app.application.photo_service import PhotoService
from app.core.config import get_settings
from app.core.errors import NotFoundError, ValidationError
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import get_object_storage
from app.infrastructure.vector_store import get_vector_store
from app.schemas.photos import PhotoEnrolledResponse, PhotoListResponse, PhotoResponse

router = APIRouter(prefix="/people/{person_id}/photos", tags=["photos"])

PhotoServiceDep = Annotated[PhotoService, Depends(get_photo_service)]


@router.post("", response_model=PhotoEnrolledResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    person_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    image: UploadFile = File(...),
) -> PhotoEnrolledResponse:
    settings = get_settings()
    content = await image.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    enroll_service = EnrollmentService(
        session=session,
        face_pipeline=FacePipeline(settings=settings),
        storage=get_object_storage(settings=settings),
        vector_store=get_vector_store(settings=settings),
        settings=settings,
    )
    photo_service = PhotoService(session=session, settings=settings)

    try:
        person, photo, identity, sample = await enroll_service.enroll(
            image_bytes=content,
            person_id=person_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    image_url = await photo_service.get_image_url(photo)
    crop_url = await photo_service.get_crop_url(
        sample.cropImageBucket,
        sample.cropImageKey,
    )

    return PhotoEnrolledResponse(
        photoId=photo.photoId,
        personId=person.personId,
        faceId=identity.faceId,
        sampleId=sample.sampleId,
        qdrantPointId=sample.qdrantPointId,
        imageUrl=image_url,
        cropImageUrl=crop_url or "",
        modelName=sample.modelName,
        modelVersion=sample.modelVersion,
        embeddingDimension=sample.embeddingDimension,
        qualityScore=sample.qualityScore,
        isIndexed=sample.isIndexed,
        createdAt=photo.createdAt,
    )


@router.get("", response_model=PhotoListResponse)
async def list_photos(
    person_id: UUID,
    service: PhotoServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PhotoListResponse:
    items, total = await service.list_by_person(person_id, limit=limit, offset=offset)
    enriched: list[PhotoResponse] = []
    for photo in items:
        photo_dict = PhotoResponse.model_validate(photo).model_dump()
        photo_dict["originalImageUrl"] = await service.get_image_url(photo)
        enriched.append(PhotoResponse(**photo_dict))

    return PhotoListResponse(
        items=enriched,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    person_id: UUID,
    photo_id: UUID,
    service: PhotoServiceDep,
) -> None:
    await service.delete(person_id, photo_id)
