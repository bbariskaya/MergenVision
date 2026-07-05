"""Person request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ListingResponse


class PersonCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    firstName: str | None = Field(None, max_length=255)
    lastName: str | None = Field(None, max_length=255)
    nationalId: str | None = Field(None, min_length=11, max_length=11, pattern=r"^\d{11}$")
    details: dict | None = None


class PersonUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    firstName: str | None = Field(None, max_length=255)
    lastName: str | None = Field(None, max_length=255)
    details: dict | None = None


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personId: UUID
    firstName: str | None
    lastName: str | None
    nationalIdMasked: str | None
    details: dict | None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime | None


class PersonListResponse(ListingResponse[PersonResponse]):
    pass
