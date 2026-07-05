"""Qdrant async client factory."""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.core.config import Settings, get_settings

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client(settings: Settings | None = None) -> AsyncQdrantClient:
    """Return a singleton async Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        config = settings or get_settings()
        _qdrant_client = AsyncQdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key or None,
        )
    return _qdrant_client
