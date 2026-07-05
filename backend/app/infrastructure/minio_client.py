"""MinIO client factory."""

from __future__ import annotations

from minio import Minio

from app.core.config import Settings, get_settings

_minio_client: Minio | None = None


def get_minio_client(settings: Settings | None = None) -> Minio:
    """Return a singleton MinIO client."""
    global _minio_client
    if _minio_client is None:
        config = settings or get_settings()
        _minio_client = Minio(
            config.minio_url,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=config.minio_secure,
        )
    return _minio_client
