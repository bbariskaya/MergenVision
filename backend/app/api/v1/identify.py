"""Identification endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.application.identification_service import IdentificationService
from app.core.config import get_settings
from app.core.errors import ValidationError
from app.domain.models import Person
from app.infrastructure.adapters.pipelines import FacePipeline
from app.infrastructure.storage import get_object_storage
from app.infrastructure.vector_store import get_vector_store
from app.schemas.identify import (
    IdentificationRequestListResponse,
    IdentifyQueryParams,
    IdentifyResponse,
)
from sqlalchemy import select

async def _resolve_candidate_names(
    session: AsyncSession,
    response: IdentifyResponse,
) -> None:
    """Fill candidate.name fields from the person records."""
    person_ids: set[UUID] = set()
    for face in response.faces:
        if face.result and face.result.personId:
            person_ids.add(face.result.personId)
        for candidate in face.candidates:
            if candidate.personId:
                person_ids.add(candidate.personId)

    if not person_ids:
        return

    stmt = select(
        Person.personId,
        Person.firstName,
        Person.lastName,
    ).where(Person.personId.in_(person_ids), Person.isActive.is_(True))
    result = await session.execute(stmt)
    names = {
        row.personId: " ".join(filter(None, [row.firstName, row.lastName])).strip()
        for row in result.mappings().all()
    }

    for face in response.faces:
        if face.result and face.result.personId and face.result.personId in names:
            face.result.name = names[face.result.personId]
        for candidate in face.candidates:
            if candidate.personId and candidate.personId in names:
                candidate.name = names[candidate.personId]


router = APIRouter(tags=["identification"])


@router.post("/identify", response_model=IdentifyResponse)
async def identify(
    session: Annotated[AsyncSession, Depends(get_db)],
    image: UploadFile = File(...),
    params: IdentifyQueryParams = Depends(),
) -> IdentifyResponse:
    settings = get_settings()
    content = await image.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    service = IdentificationService(
        session=session,
        face_pipeline=FacePipeline(settings=settings),
        storage=get_object_storage(settings=settings),
        vector_store=get_vector_store(settings=settings),
        settings=settings,
    )
    try:
        response = await service.identify(
            image_bytes=content,
            top_k=params.topK,
            threshold=params.threshold,
            selected_face_index=params.selectedFaceIndex,
        )
        await _resolve_candidate_names(session, response)
        return response
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/identification-requests", response_model=IdentificationRequestListResponse)
async def list_requests(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> IdentificationRequestListResponse:
    service = IdentificationService(
        session=session,
        settings=get_settings(),
    )
    items, total = await service.list(limit=limit, offset=offset)
    return IdentificationRequestListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/identification-requests/{request_id}", response_model=IdentifyResponse)
async def get_request(
    request_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IdentifyResponse:
    service = IdentificationService(
        session=session,
        settings=get_settings(),
    )
    response = await service.get(request_id)
    await _resolve_candidate_names(session, response)
    return response
