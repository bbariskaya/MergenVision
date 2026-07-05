# 07 REST API Contract Implementation Plan

> **Reference-first sources:** `docs/architecture/API_CONTRACT.md`, `docs/architecture/PHASE_IMPLEMENTATION_GATES.md`, `docs/architecture/NO_SCOPE_CREEP_RULES.md`, `docs/architecture/FUTURE_BOUNDARIES.md`.

## Goal

Map the Phase 1 allowed routes to concrete FastAPI routers and response schemas. No placeholder or future routes are added.

## Phase 1 allowed routes

```text
GET    /health
GET    /ready
POST   /people
GET    /people
GET    /people/{personId}
PATCH  /people/{personId}
DELETE /people/{personId}
POST   /people/{personId}/photos
GET    /people/{personId}/photos
DELETE /people/{personId}/photos/{photoId}
POST   /identify
GET    /identification-requests
GET    /identification-requests/{requestId}
GET    /audit
GET    /stats
GET    /media/{bucket}/{objectKey}
```

## Forbidden routes

```text
/videos/*
/imports/*
/faces/*
/oracle/*
/objects/*
/streams/*
any 501 placeholder route
any OpenAPI exposure for future endpoints
```

## Router mapping

| Route | Handler file | Handler function | Service |
|-------|--------------|------------------|---------|
| `GET /health` | `api/v1/health.py` | `health()` | none |
| `GET /ready` | `api/v1/health.py` | `ready(db, qdrant, minio)` | infrastructure checks |
| `POST /people` | `api/v1/people.py` | `create_person(...)` | `PeopleService.create` |
| `GET /people` | `api/v1/people.py` | `list_people(...)` | `PeopleService.list` |
| `GET /people/{personId}` | `api/v1/people.py` | `get_person(...)` | `PeopleService.get` |
| `PATCH /people/{personId}` | `api/v1/people.py` | `update_person(...)` | `PeopleService.update` |
| `DELETE /people/{personId}` | `api/v1/people.py` | `delete_person(...)` | `PeopleService.delete` |
| `POST /people/{personId}/photos` | `api/v1/photos.py` | `upload_photo(...)` | `PhotoService.upload` |
| `GET /people/{personId}/photos` | `api/v1/photos.py` | `list_photos(...)` | `PhotoService.list` |
| `DELETE /people/{personId}/photos/{photoId}` | `api/v1/photos.py` | `delete_photo(...)` | `PhotoService.delete` |
| `POST /identify` | `api/v1/identify.py` | `identify(...)` | `IdentifyService.identify` |
| `GET /identification-requests` | `api/v1/identification_requests.py` | `list_requests(...)` | `IdentifyService.list` |
| `GET /identification-requests/{requestId}` | `api/v1/identification_requests.py` | `get_request(...)` | `IdentifyService.get` |
| `GET /audit` | `api/v1/audit.py` | `list_audit(...)` | `AuditService.list` |
| `GET /stats` | `api/v1/stats.py` | `get_stats(...)` | `StatsService.get` |
| `GET /media/{bucket}/{objectKey}` | `api/v1/media.py` | `get_media(...)` | MinIO presigned URL |

## Request/response schemas

- `app/schemas/people.py`: `PersonCreate`, `PersonUpdate`, `PersonResponse`, `PersonListResponse`.
- `app/schemas/photos.py`: `PhotoUploadForm`, `PhotoResponse`, `PhotoListResponse`.
- `app/schemas/identify.py`: `IdentifyRequest`, `IdentifyResponse`, `IdentificationRequestResponse`.
- `app/schemas/audit.py`: `AuditEntryResponse`, `AuditListResponse`.
- `app/schemas/stats.py`: `StatsResponse`.
- `app/schemas/common.py`: `ErrorResponse`, pagination helpers.

## Dependencies per router

- `db: AsyncSession` from `app.api.dependencies.get_db`.
- `qdrant: QdrantClient` from `app.api.dependencies.get_qdrant_client`.
- `minio: Minio` from `app.api.dependencies.get_minio_client`.
- `adapters: ModelAdapterProvider` from `app.api.dependencies.get_adapters`.
- Services are constructed from these dependencies inside the route or in dedicated dependency builders.

## How MergenVision will adapt this

- All routes are `async def` and delegate to services; routes contain no business logic.
- `GET /ready` performs lightweight checks: PostgreSQL query, Qdrant collection existence, MinIO bucket existence. It does **not** run model inference.
- `POST /people/{personId}/photos` accepts `multipart/form-data`, streams `UploadFile` to service, returns `PhotoResponse` only after enrollment pipeline completes.
- `POST /identify` accepts `multipart/form-data`, runs the identification pipeline synchronously, returns `IdentifyResponse`.
- `GET /media/{bucket}/{objectKey}` validates the bucket is in an allowlist (`people-photos`, `face-crops`, `query-images`), validates the object key pattern, then redirects to a short-lived presigned URL.
- No route returns raw embeddings or full sensitive person details.

## Files to be created in later phases

- `backend/app/schemas/*.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/health.py`
- `backend/app/api/v1/people.py`
- `backend/app/api/v1/photos.py`
- `backend/app/api/v1/identify.py`
- `backend/app/api/v1/identification_requests.py`
- `backend/app/api/v1/audit.py`
- `backend/app/api/v1/stats.py`
- `backend/app/api/v1/media.py`

## Verification plan

- Run `fastapi dev` or `uvicorn` and verify OpenAPI docs show only allowed routes.
- Smoke test each route with `httpx`/`curl` against test containers.
- Confirm `GET /openapi.json` does not expose forbidden paths.
