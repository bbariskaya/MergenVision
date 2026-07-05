"""People application service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_national_id, mask_national_id
from app.domain.models import Person
from app.repositories.face_identity_repo import FaceIdentityRepository
from app.repositories.face_sample_repo import FaceSampleRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.photo_repo import PhotoRepository
from app.schemas.people import PersonCreate, PersonUpdate


class PeopleService:
    """Business operations for person identities."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = PersonRepository(session)
        self._photo_repo = PhotoRepository(session)
        self._identity_repo = FaceIdentityRepository(session)
        self._sample_repo = FaceSampleRepository(session)

    async def create(self, data: PersonCreate) -> Person:
        national_id_hash: str | None = None
        national_id_masked: str | None = None
        if data.nationalId is not None:
            national_id_hash = hash_national_id(data.nationalId)
            exists = await self._repo.exists_by_national_id_hash(national_id_hash)
            if exists:
                raise ConflictError("Person with this national ID already exists")
            national_id_masked = mask_national_id(data.nationalId)

        return await self._repo.create(
            first_name=data.firstName,
            last_name=data.lastName,
            national_id_hash=national_id_hash,
            national_id_masked=national_id_masked,
            details=data.details,
        )

    async def get(self, person_id: UUID) -> Person:
        person = await self._repo.get_by_id(person_id)
        if person is None:
            raise NotFoundError("Person not found")
        return person

    async def list(self, limit: int, offset: int) -> tuple[list[Person], int]:
        return await self._repo.list_active(limit=limit, offset=offset)

    async def update(self, person_id: UUID, data: PersonUpdate) -> Person:
        person = await self.get(person_id)
        return await self._repo.update(
            person,
            firstName=data.firstName,
            lastName=data.lastName,
            details=data.details,
        )

    async def delete(self, person_id: UUID) -> bool:
        deleted = await self._repo.soft_delete(person_id)
        if not deleted:
            raise NotFoundError("Person not found")
        await self._photo_repo.soft_delete_by_person(person_id)
        await self._identity_repo.soft_delete_by_person(person_id)
        await self._sample_repo.soft_delete_by_person(person_id)
        return True
