"""OpenAPI scope safety tests."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_openapi_exposes_only_allowed_routes(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200

    paths = set(response.json().get("paths", {}))
    allowed = {
        "/health",
        "/ready",
        "/people",
        "/people/{person_id}",
        "/people/{person_id}/photos",
        "/people/{person_id}/photos/{photo_id}",
        "/identify",
        "/identification-requests",
        "/identification-requests/{request_id}",
        "/audit",
        "/stats",
        "/media/{bucket}/{object_key}",
    }
    forbidden_prefixes = (
        "/videos/",
        "/imports/",
        "/faces/",
        "/oracle/",
        "/objects/",
        "/streams/",
    )

    assert paths <= allowed, f"Unexpected routes exposed: {paths - allowed}"
    for prefix in forbidden_prefixes:
        assert not any(
            path.startswith(prefix) for path in paths
        ), f"Forbidden route prefix {prefix!r} exposed"
