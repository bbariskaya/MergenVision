"""Aggregate all v1 routers."""

from fastapi import APIRouter

from app.api.v1 import audit, health, identify, media, people, photos, stats

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(people.router, tags=["people"])
api_router.include_router(photos.router, tags=["photos"])
api_router.include_router(identify.router, tags=["identification"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(stats.router, tags=["stats"])
api_router.include_router(media.router, tags=["media"])
