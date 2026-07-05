"""Audit log repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        action: str,
        entity_type: str | None,
        entity_id: UUID | None,
        actor: str | None,
        request_id: UUID | None,
        outcome: str,
        safe_metadata: dict[str, Any] | None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            entityType=entity_type,
            entityId=entity_id,
            actor=actor,
            requestId=request_id,
            outcome=outcome,
            safeMetadata=safe_metadata,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_filtered(
        self,
        entity_type: str | None,
        entity_id: UUID | None,
        action: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        where = AuditLog.createdAt.is_not(None)
        if entity_type:
            where = where & (AuditLog.entityType == entity_type)
        if entity_id:
            where = where & (AuditLog.entityId == entity_id)
        if action:
            where = where & (AuditLog.action == action)

        stmt = (
            select(AuditLog)
            .where(where)
            .order_by(desc(AuditLog.createdAt))
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(AuditLog).where(where)
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        return list(result.scalars().all()), int(count_result.scalar() or 0)
