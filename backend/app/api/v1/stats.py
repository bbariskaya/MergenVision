"""Stats endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_stats_service
from app.application.stats_service import StatsService
from app.schemas.stats import StatsResponse

router = APIRouter(tags=["stats"])

ServiceDep = Annotated[StatsService, Depends(get_stats_service)]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(service: ServiceDep) -> StatsResponse:
    data = await service.get()
    return StatsResponse(**data)
