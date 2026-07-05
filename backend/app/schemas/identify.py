"""Identification request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ListingResponse


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Candidate(BaseModel):
    rank: int
    faceId: UUID | None
    personId: UUID | None
    sampleId: UUID | None
    name: str | None
    score: float
    decision: str
    cropImageUrl: str | None = None


class IdentifyFaceResult(BaseModel):
    queryFaceId: UUID
    boundingBox: BoundingBox
    qualityScore: float | None
    result: Candidate | None
    candidates: list[Candidate]


class IdentifyResponse(BaseModel):
    requestId: UUID
    status: str
    decision: str | None
    faceCount: int | None
    queryImageUrl: str | None
    faces: list[IdentifyFaceResult]
    createdAt: datetime
    completedAt: datetime | None


class IdentificationRequestSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requestId: UUID
    status: str
    decision: str | None
    faceCount: int | None
    topK: int
    createdAt: datetime
    completedAt: datetime | None


class IdentificationRequestListResponse(ListingResponse[IdentificationRequestSummary]):
    pass


class IdentifyQueryParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    topK: int = Field(default=5, ge=1, le=20)
    selectedFaceIndex: int | None = Field(default=None, ge=0)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)
