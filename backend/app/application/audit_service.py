"""Audit log application service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog
from app.repositories.audit_repo import AuditRepository


class AuditService:
    """Read-only audit log operations (write via repository)."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditRepository(session)

    async def list(
        self,
        entity_type: str | None,
        entity_id: UUID | None,
        action: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        return await self._repo.list_filtered(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            limit=limit,
            offset=offset,
        )
