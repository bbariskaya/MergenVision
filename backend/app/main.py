"""FastAPI application factory for MergenVision."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.log_level)

    from app.infrastructure.adapters.pipelines import FacePipeline
    from app.infrastructure.db import get_db_engine
    from app.infrastructure.minio_client import get_minio_client
    from app.infrastructure.qdrant_client import get_qdrant_client
    from app.infrastructure.runtime_state import mark_runtime_loaded
    from app.infrastructure.storage import ObjectStorage
    from app.infrastructure.vector_store import VectorStore

    engine = get_db_engine()
    minio_client = get_minio_client(settings)
    qdrant_client = get_qdrant_client(settings)

    storage = ObjectStorage(client=minio_client, settings=settings)
    await storage.ensure_bucket(settings.minio_bucket_people_photos)
    await storage.ensure_bucket(settings.minio_bucket_face_crops)
    await storage.ensure_bucket(settings.minio_bucket_query_images)

    vector_store = VectorStore(client=qdrant_client, settings=settings)
    await vector_store.ensure_collection(
        settings.recognizer_model_name,
        settings.recognizer_embedding_dimension,
        settings.recognizer_version,
    )

    FacePipeline(settings=settings)
    mark_runtime_loaded()

    yield

    await qdrant_client.close()
    await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    config = settings or get_settings()

    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
        lifespan=lifespan,
    )

    app.include_router(api_router)

    return app
