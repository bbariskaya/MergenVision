"""Health and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_readiness_service
from app.application.readiness_service import ReadinessService
from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()

ReadinessServiceDep = Annotated[ReadinessService, Depends(get_readiness_service)]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return a lightweight liveness probe response."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(service: ReadinessServiceDep) -> ReadyResponse:
    """Return readiness state by checking critical dependencies."""
    return await service.check()
