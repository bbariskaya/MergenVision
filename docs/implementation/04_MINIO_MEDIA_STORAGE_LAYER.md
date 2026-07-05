# 04 MinIO Media Storage Layer

> **Reference-first sources:** `docs/architecture/DATA_MODEL.md`, `docs/architecture/SENSITIVE_DATA_RULES.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`, Context7 (MinIO), deepwiki `minio/minio-py`.

## Goal

Use MinIO as the object store for original images, face crops, and query images. PostgreSQL stores only bucket/object keys and content metadata. MinIO never receives full person metadata or embeddings.

## Buckets

| Bucket | Content | Retention policy |
|--------|---------|------------------|
| `people-photos` | Original uploaded person photos | Until person/photo is soft-deleted |
| `face-crops` | Cropped face chips extracted during enrollment | Until associated sample is removed |
| `query-images` | Optional retained query images for audit | configurable TTL; default delete after request completion |

Bucket names must be configurable via environment variables for multi-environment deployments.

## How others implement this

The `minio/minio-py` SDK patterns:

- Initialize `Minio` with endpoint, access key, and secret key.

```python
from minio import Minio

client = Minio("minio:9000", access_key="...", secret_key="...", secure=False)
```

- Create bucket if absent:

```python
if not client.bucket_exists("my-bucket"):
    client.make_bucket("my-bucket")
```

- Upload from a stream:

```python
client.put_object(bucket, object_name, data=stream, length=length, content_type="image/jpeg")
```

- Generate presigned URLs:

```python
url = client.presigned_get_object("my-bucket", "my-object", expires=timedelta(hours=2))
url = client.presigned_put_object("my-bucket", "my-object", expires=timedelta(hours=2))
```

- In FastAPI, the client instance is typically initialized once and injected into route handlers.

## How MergenVision will adapt this

- **Client lifecycle**: single `Minio` instance created in `app/infrastructure/minio_client.py` at startup.
- **Object key naming**: `{bucket}/{personId}/{photoId}/{filename}` for originals; deterministic IDs for crops and queries; no user-controlled characters in object keys.
- **Upload flow**:
  1. Route streams `UploadFile` to `PhotoService`.
  2. `ImageValidator` checks mime type, size, dimensions.
  3. Object is uploaded to `people-photos`.
  4. PostgreSQL `person_photo` row stores `bucket`, `objectKey`, `contentType`, `sizeBytes`, `width`, `height`.
- **Presigned GET for media route**: `GET /media/{bucket}/{objectKey}` proxies or redirects to a short-lived presigned URL. Phase 1 implementation returns a 307 redirect to the presigned URL, keeping the API contract clean.
- **Retention**:
  - Soft-deleted photos keep objects until a background cleanup job runs (Phase 2/3), or an admin purge endpoint is added later.
  - Query images are deleted immediately after request completion unless `retainQueryImage=true` is enabled and a TTL is configured.
- **Content validation**: reject non-image uploads before touching MinIO. Max file size enforced by dependency.
- **No public bucket policy**: access only via presigned URLs or internal service credentials.

## Files to be created in later phases

- `backend/app/infrastructure/minio_client.py`
- `backend/app/application/photo_service.py`
- `backend/app/api/v1/media.py`

## Verification plan

- Integration tests with local MinIO container:
  - upload image,
  - fetch via presigned URL,
  - delete object,
  - verify object does not exist.
- Confirm object keys do not include user input.
