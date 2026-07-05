"""Photo and enrollment response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ListingResponse


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    photoId: UUID
    personId: UUID
    originalImageUrl: str | None = None
    contentType: str
    sizeBytes: int
    width: int | None
    height: int | None
    isActive: bool
    createdAt: datetime


class PhotoEnrolledResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    photoId: UUID
    personId: UUID
    faceId: UUID
    sampleId: UUID
    qdrantPointId: UUID
    imageUrl: str
    cropImageUrl: str
    modelName: str
    modelVersion: str
    embeddingDimension: int
    qualityScore: float | None
    isIndexed: bool
    createdAt: datetime


class PhotoListResponse(ListingResponse[PhotoResponse]):
    pass
