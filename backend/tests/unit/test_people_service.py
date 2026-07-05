"""Unit tests for PeopleService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.people_service import PeopleService
from app.core.errors import ConflictError, NotFoundError
from app.domain.models import Person
from app.schemas.people import PersonCreate, PersonUpdate


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def service(mock_session):
    svc = PeopleService(mock_session)
    svc._repo = MagicMock()
    svc._photo_repo = MagicMock()
    svc._identity_repo = MagicMock()
    svc._sample_repo = MagicMock()
    return svc


def _make_person(**kwargs) -> Person:
    person = MagicMock(spec=Person)
    person.personId = kwargs.get("person_id", uuid4())
    person.firstName = kwargs.get("first_name", "Foo")
    person.lastName = kwargs.get("last_name", "Bar")
    person.nationalIdHash = kwargs.get("national_id_hash")
    person.nationalIdMasked = kwargs.get("national_id_masked")
    person.details = kwargs.get("details")
    person.isActive = True
    return person


@pytest.mark.asyncio
async def test_create_hashes_and_masks_national_id(service):
    data = PersonCreate(firstName="Barış", lastName="Özcan", nationalId="12345678901")
    service._repo.exists_by_national_id_hash = AsyncMock(return_value=False)
    created = _make_person(
        person_id=data.nationalId,
        first_name=data.firstName,
        last_name=data.lastName,
    )
    created.nationalIdHash = "hashed"
    created.nationalIdMasked = "*******8901"
    service._repo.create = AsyncMock(return_value=created)

    result = await service.create(data)

    service._repo.exists_by_national_id_hash.assert_awaited_once()
    call_args = service._repo.create.call_args.kwargs
    assert call_args["first_name"] == data.firstName
    assert call_args["last_name"] == data.lastName
    assert call_args["national_id_hash"] != data.nationalId
    assert len(call_args["national_id_hash"]) == 64
    assert call_args["national_id_masked"] == "*******8901"
    assert result is created


@pytest.mark.asyncio
async def test_create_raises_conflict_for_duplicate_national_id(service):
    data = PersonCreate(firstName="Barış", lastName="Özcan", nationalId="12345678901")
    service._repo.exists_by_national_id_hash = AsyncMock(return_value=True)

    with pytest.raises(ConflictError):
        await service.create(data)

    service._repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_without_national_id(service):
    data = PersonCreate(firstName="Jane", lastName="Doe")
    created = _make_person(first_name=data.firstName, last_name=data.lastName)
    service._repo.create = AsyncMock(return_value=created)

    result = await service.create(data)

    service._repo.exists_by_national_id_hash.assert_not_called()
    call_args = service._repo.create.call_args.kwargs
    assert call_args["national_id_hash"] is None
    assert call_args["national_id_masked"] is None
    assert result is created


@pytest.mark.asyncio
async def test_get_returns_person(service):
    person_id = uuid4()
    person = _make_person(person_id=person_id)
    service._repo.get_by_id = AsyncMock(return_value=person)

    result = await service.get(person_id)

    assert result is person


@pytest.mark.asyncio
async def test_get_raises_not_found(service):
    service._repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.get(uuid4())


@pytest.mark.asyncio
async def test_list_delegates_to_repo(service):
    person = _make_person()
    service._repo.list_active = AsyncMock(return_value=([person], 1))

    items, total = await service.list(limit=20, offset=0)

    assert items == [person]
    assert total == 1
    service._repo.list_active.assert_awaited_once_with(limit=20, offset=0)


@pytest.mark.asyncio
async def test_update_delegates_to_repo(service):
    person_id = uuid4()
    person = _make_person(person_id=person_id, first_name="Old")
    updated = _make_person(person_id=person_id, first_name="New")
    service._repo.get_by_id = AsyncMock(return_value=person)
    service._repo.update = AsyncMock(return_value=updated)

    result = await service.update(person_id, PersonUpdate(firstName="New"))

    service._repo.update.assert_awaited_once_with(
        person,
        firstName="New",
        lastName=None,
        details=None,
    )
    assert result is updated


@pytest.mark.asyncio
async def test_delete_soft_deletes_cascade(service):
    person_id = uuid4()
    service._repo.soft_delete = AsyncMock(return_value=True)
    service._photo_repo.soft_delete_by_person = AsyncMock()
    service._identity_repo.soft_delete_by_person = AsyncMock()
    service._sample_repo.soft_delete_by_person = AsyncMock()

    result = await service.delete(person_id)

    assert result is True
    service._photo_repo.soft_delete_by_person.assert_awaited_once_with(person_id)
    service._identity_repo.soft_delete_by_person.assert_awaited_once_with(person_id)
    service._sample_repo.soft_delete_by_person.assert_awaited_once_with(person_id)


@pytest.mark.asyncio
async def test_delete_raises_not_found(service):
    service._repo.soft_delete = AsyncMock(return_value=False)

    with pytest.raises(NotFoundError):
        await service.delete(uuid4())
