from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON  # noqa: N811
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import Uuid

from app.infrastructure.db import Base


def _make_metadata_sqlite_compatible() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = SQLiteJSON()
            elif isinstance(column.type, PgUUID):
                column.type = Uuid(as_uuid=True)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    _make_metadata_sqlite_compatible()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()
