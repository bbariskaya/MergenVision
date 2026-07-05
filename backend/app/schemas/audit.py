"""Audit log schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ListingResponse


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    auditId: UUID
    action: str
    entityType: str | None
    entityId: UUID | None
    actor: str | None
    requestId: UUID | None
    outcome: str
    safeMetadata: dict | None
    createdAt: datetime


class AuditListResponse(ListingResponse[AuditEntry]):
    pass
