"""Person repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid7
from app.domain.models import Person


class PersonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(
        self,
        persons: list[Person],
        chunk_size: int = 1000,
    ) -> list[Person]:
        """Insert many persons in chunked statements.

        asyncpg has a 32767 parameter limit per query. Chunking keeps large
        identity-folder enrollments (10k+ persons) from hitting that limit.
        """
        if not persons:
            return []
        table = Person.__table__
        for person in persons:
            if person.personId is None:
                person.personId = new_uuid7()
            if person.isActive is None:
                person.isActive = True
        now = datetime.now(UTC)

        for i in range(0, len(persons), chunk_size):
            chunk = persons[i : i + chunk_size]
            values = []
            for person in chunk:
                row = {col.key: getattr(person, col.key) for col in table.columns}
                if row.get("createdAt") is None:
                    row["createdAt"] = now
                if row.get("updatedAt") is None:
                    row["updatedAt"] = now
                values.append(row)
            await self._session.execute(insert(table).values(values))

        return persons

    async def create(
        self,
        first_name: str | None,
        last_name: str | None,
        national_id_hash: str | None,
        national_id_masked: str | None,
        details: dict | None,
    ) -> Person:
        person = Person(
            firstName=first_name,
            lastName=last_name,
            nationalIdHash=national_id_hash,
            nationalIdMasked=national_id_masked,
            details=details,
        )
        self._session.add(person)
        await self._session.flush()
        return person

    async def get_by_id(self, person_id: UUID) -> Person | None:
        stmt = select(Person).where(Person.personId == person_id, Person.isActive.is_(True))
        return await self._session.scalar(stmt)

    async def list_active(self, limit: int, offset: int) -> tuple[list[Person], int]:
        where = Person.isActive.is_(True)
        stmt = (
            select(Person)
            .where(where)
            .order_by(Person.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(Person).where(where)
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)

    async def update(self, person: Person, **fields: object) -> Person:
        for key, value in fields.items():
            if value is not None and hasattr(person, key):
                setattr(person, key, value)
        await self._session.flush()
        return person

    async def soft_delete(self, person_id: UUID) -> bool:
        person = await self.get_by_id(person_id)
        if person is None:
            return False
        person.isActive = False
        person.deletedAt = datetime.now(UTC)
        await self._session.flush()
        return True

    async def exists_by_national_id_hash(self, national_id_hash: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(Person)
            .where(
                Person.nationalIdHash == national_id_hash,
                Person.isActive.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0) > 0
