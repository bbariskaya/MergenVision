"""SQLAlchemy 2.0 async database foundation."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all future ORM models."""


@lru_cache(maxsize=1)
def get_db_engine() -> AsyncEngine:
    """Return a cached async database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return a cached async session factory bound to the current engine."""
    return async_sessionmaker(
        get_db_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


AsyncSessionLocal = get_async_session_maker()
