"""Stats response schema."""

from pydantic import BaseModel


class StatsResponse(BaseModel):
    personCount: int
    photoCount: int
    faceSampleCount: int
    identificationRequestCount: int
