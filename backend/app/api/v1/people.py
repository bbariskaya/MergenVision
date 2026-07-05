"""People endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_people_service
from app.application.people_service import PeopleService
from app.schemas.people import PersonCreate, PersonListResponse, PersonResponse, PersonUpdate

router = APIRouter(prefix="/people", tags=["people"])

ServiceDep = Annotated[PeopleService, Depends(get_people_service)]


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(service: ServiceDep, data: PersonCreate) -> PersonResponse:
    person = await service.create(data)
    return PersonResponse.model_validate(person)


@router.get("", response_model=PersonListResponse)
async def list_people(
    service: ServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PersonListResponse:
    items, total = await service.list(limit=limit, offset=offset)
    return PersonListResponse(
        items=[PersonResponse.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(service: ServiceDep, person_id: UUID) -> PersonResponse:
    person = await service.get(person_id)
    return PersonResponse.model_validate(person)


@router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    service: ServiceDep,
    person_id: UUID,
    data: PersonUpdate,
) -> PersonResponse:
    person = await service.update(person_id, data)
    return PersonResponse.model_validate(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(service: ServiceDep, person_id: UUID) -> None:
    await service.delete(person_id)
