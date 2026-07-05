"""MinIO object storage operations."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, StorageError
from app.infrastructure.minio_client import get_minio_client


@dataclass(frozen=True)
class UploadItem:
    """A single object to upload concurrently."""

    bucket: str
    key: str
    data: bytes
    content_type: str = "application/octet-stream"


class ObjectStorage:
    """Thin wrapper around the MinIO client."""

    def __init__(
        self,
        client: Minio | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or get_minio_client(self._settings)
        self._public_client: Minio | None = None
        if self._settings.minio_public_url:
            # A separate client for presigned URL generation only. Region is
            # pinned so MinIO does not try to contact the public endpoint.
            self._public_client = Minio(
                self._settings.minio_public_url,
                access_key=self._settings.minio_access_key,
                secret_key=self._settings.minio_secret_key,
                secure=self._settings.minio_secure,
                region="us-east-1",
            )

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        length: int | None = None,
    ) -> None:
        """Upload bytes to a bucket."""
        try:
            found = self._client.bucket_exists(bucket)
            if not found:
                self._client.make_bucket(bucket)
            self._client.put_object(
                bucket,
                key,
                BytesIO(data),
                length=length or len(data),
                content_type=content_type,
            )
        except S3Error as exc:
            raise StorageError(f"Failed to upload {bucket}/{key}: {exc}") from exc

    async def upload_concurrent(
        self,
        items: Sequence[UploadItem],
        max_concurrency: int = 128,
    ) -> list[str]:
        """Upload many objects concurrently using a thread-pool for sync MinIO.

        Concurrency is capped to avoid swamping MinIO with thousands of
        simultaneous uploads. Buckets are assumed to exist (callers should use
        ``ensure_bucket`` first); this avoids a redundant ``bucket_exists``
        round-trip per object.
        """
        if not items:
            return []

        sem = asyncio.Semaphore(max_concurrency)

        async def _upload_one(item: UploadItem) -> str:
            async with sem:
                return await asyncio.to_thread(self._sync_upload_item, item)

        results = await asyncio.gather(
            *[_upload_one(item) for item in items],
            return_exceptions=True,
        )

        keys: list[str] = []
        for item, result in zip(items, results, strict=True):
            if isinstance(result, Exception):
                raise StorageError(
                    f"Failed to upload {item.bucket}/{item.key}: {result}"
                ) from result
            keys.append(item.key)
        return keys

    def _sync_upload_item(self, item: UploadItem) -> str:
        self._client.put_object(
            item.bucket,
            item.key,
            BytesIO(item.data),
            length=len(item.data),
            content_type=item.content_type,
        )
        return item.key

    async def get_object(self, bucket: str, key: str) -> bytes:
        """Return object bytes."""
        try:
            response = self._client.get_object(bucket, key)
            return bytes(response.read())
        except S3Error as exc:
            if exc.code in ("NoSuchKey", "NoSuchBucket"):
                raise NotFoundError(f"Object not found: {bucket}/{key}") from exc
            raise StorageError(f"Failed to get {bucket}/{key}: {exc}") from exc

    async def delete(self, bucket: str, key: str) -> None:
        """Delete an object; ignores 404."""
        try:
            self._client.remove_object(bucket, key)
        except S3Error as exc:
            if exc.code in ("NoSuchKey", "NoSuchBucket"):
                return
            raise StorageError(f"Failed to delete {bucket}/{key}: {exc}") from exc

    async def presigned_get_url(self, bucket: str, key: str, expires: int | None = None) -> str:
        """Return a presigned GET URL (public endpoint when configured)."""
        seconds = expires if expires is not None else self._settings.minio_url_expiry_seconds
        client = self._public_client or self._client
        try:
            return client.presigned_get_object(
                bucket,
                key,
                expires=timedelta(seconds=seconds),
            )
        except S3Error as exc:
            raise StorageError(f"Failed to presign {bucket}/{key}: {exc}") from exc

    async def ensure_bucket(self, bucket: str) -> None:
        """Create the bucket if it does not exist."""
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error as exc:
            raise StorageError(f"Failed to ensure bucket {bucket}: {exc}") from exc


def get_object_storage(
    client: Minio | None = None,
    settings: Settings | None = None,
) -> ObjectStorage:
    return ObjectStorage(client=client, settings=settings)
