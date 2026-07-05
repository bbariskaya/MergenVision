"""Dependency health checks for readiness endpoint."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings, get_settings
from app.infrastructure.db import get_db_engine
from app.infrastructure.minio_client import get_minio_client
from app.infrastructure.qdrant_client import get_qdrant_client
from app.infrastructure.runtime_state import is_runtime_loaded


class HealthChecks:
    """Async readiness checks for PostgreSQL, Qdrant, MinIO, and runtime."""

    def __init__(
        self,
        engine: AsyncEngine | None = None,
        settings: Settings | None = None,
        runtime_loaded: bool | None = None,
    ) -> None:
        self._engine = engine or get_db_engine()
        self._settings = settings or get_settings()
        self._runtime_loaded_override = runtime_loaded

    def _is_runtime_loaded(self) -> bool:
        if self._runtime_loaded_override is not None:
            return self._runtime_loaded_override
        return is_runtime_loaded()

    async def check_postgres(self) -> bool:
        try:
            from sqlalchemy.ext.asyncio import AsyncSession

            async with AsyncSession(self._engine) as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception:
            return False

    async def check_qdrant(self) -> bool:
        try:
            client = get_qdrant_client(self._settings)
            await client.get_collections()
            return True
        except Exception:
            return False

    async def check_minio(self) -> bool:
        try:
            client = get_minio_client(self._settings)
            client.list_buckets()
            return True
        except Exception:
            return False

    async def check_runtime(self) -> bool:
        return self._is_runtime_loaded()

    async def all_checks(self) -> dict[str, bool]:
        return {
            "postgres": await self.check_postgres(),
            "qdrant": await self.check_qdrant(),
            "minio": await self.check_minio(),
            "runtime": await self.check_runtime(),
        }
