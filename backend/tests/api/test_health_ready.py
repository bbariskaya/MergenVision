"""Tests for /health and /ready endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_expected_shape(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in {"ready", "not_ready"}
    assert "instanceId" in data
    assert isinstance(data["instanceId"], str)
    assert "dependencies" in data
    assert set(data["dependencies"].keys()) == {"postgres", "qdrant", "minio"}
