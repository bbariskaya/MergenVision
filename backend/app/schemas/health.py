"""Health and readiness schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    instanceId: str
    dependencies: dict[str, str]
