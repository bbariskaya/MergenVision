"""Media proxy endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from minio import Minio

from app.api.dependencies import get_object_storage_dep
from app.infrastructure.storage import ObjectStorage

router = APIRouter(tags=["media"])


@router.get("/media/{bucket}/{object_key:path}", response_model=None)
async def get_media(
    bucket: str,
    object_key: str,
    request: Request,
    storage: ObjectStorage = Depends(get_object_storage_dep),
) -> RedirectResponse | StreamingResponse:
    """Return a presigned redirect for the requested object."""
    try:
        url = await storage.presigned_get_url(bucket=bucket, key=object_key)
        if "download" in request.query_params:
            client: Minio = storage._client  # noqa: SLF001
            response = client.get_object(bucket, object_key)
            return StreamingResponse(
                iter([response.data]),
                media_type=response.getheader("Content-Type", "application/octet-stream"),
            )
        return RedirectResponse(url=url)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Media not found") from exc
