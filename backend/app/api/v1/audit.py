"""Audit endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service
from app.application.audit_service import AuditService
from app.schemas.audit import AuditEntry, AuditListResponse

router = APIRouter(tags=["audit"])

ServiceDep = Annotated[AuditService, Depends(get_audit_service)]


@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    service: ServiceDep,
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AuditListResponse:
    items, total = await service.list(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    return AuditListResponse(
        items=[AuditEntry.model_validate(entry) for entry in items],
        total=total,
        limit=limit,
        offset=offset,
    )
