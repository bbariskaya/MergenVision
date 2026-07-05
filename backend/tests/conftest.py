"""Shared test fixtures."""

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create a fresh FastAPI application for the test session."""
    return create_app()


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def client(app: FastAPI) -> AsyncClient:
    """Provide an async HTTP client backed by the ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
