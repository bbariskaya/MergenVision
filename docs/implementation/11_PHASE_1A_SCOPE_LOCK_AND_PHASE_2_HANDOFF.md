# 11 Phase 1A Scope Lock and Phase 2 Handoff

> **Reference-first sources:** `docs/architecture/NO_SCOPE_CREEP_RULES.md`, `docs/architecture/FUTURE_BOUNDARIES.md`, `docs/architecture/PHASE_IMPLEMENTATION_GATES.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`.

## Goal

Explicitly lock Phase 1A scope, list every construction task that is forbidden in Phase 1, and define the handoff criteria for Phase 2 video-based recognition.

## Phase 1A deliverables

- 12 planning documents under `docs/implementation/`.
- Cross-checked sources of truth from architecture, model research, and open-source references.
- No application code, no migrations, no Docker Compose, no runtime services.

## Phase 1 allowed runtime routes (repeat)

```text
GET /health
GET /ready
POST /people
GET /people
GET /people/{personId}
PATCH /people/{personId}
DELETE /people/{personId}
POST /people/{personId}/photos
GET /people/{personId}/photos
DELETE /people/{personId}/photos/{photoId}
POST /identify
GET /identification-requests
GET /identification-requests/{requestId}
GET /audit
GET /stats
GET /media/{bucket}/{objectKey}
```

## Phase 1 allowed tables (repeat)

```text
person
person_photo
face_sample
identification_request
identification_query_face
identification_result
audit_log
```

## Forbidden in Phase 1

### Routes

```textn/videos/*
/imports/*
/faces/*
/oracle/*
/objects/*
/streams/*
any 501 placeholder route
any OpenAPI exposure for future endpoints
```

### Tables

```text
video_job
video_track
face_video_appearance
import_job
import_job_item
anonymous_face
face_identity
object_detection_job
```

### Concepts and components

- Oracle import integration.
- Video ingestion and tracking pipelines.
- Anonymous face identity.
- Object detection.
- TensorRT optimized engine loading.
- Production 10M-shard scaling.
- RBAC, KMS, multitenancy.
- Real-image benchmark or LFW accuracy validation (Phase 1B/C, not 1A).
- Frontend production build (optional demo/admin only).

## Repository state note

- `backend/` and `frontend/` are pre-existing empty untracked directories.
- They must not receive files during Phase 1A.
- They are **not** evidence of completed scaffolding.

## Phase 1 implementation completion criteria

Before Phase 2 handoff, the following must be verified:

1. All Phase 1 routes implemented and passing integration tests.
2. `alembic upgrade head` produces exactly the seven allowed tables; none of the forbidden tables exist.
3. Qdrant collection for the active recognizer created and searchable.
4. MinIO buckets `people-photos`, `face-crops`, `query-images` functional.
5. ONNX Runtime inference works on CPU in dev and on GPU in GPU-demo mode.
6. Security/PII review passed: no embeddings in PostgreSQL, no PII in Qdrant payload, no images in audit log.
7. Code quality gates passed: `ruff`, `mypy`, test coverage ≥ 80%.

## Phase 2 handoff criteria

- Phase 1 shared identity platform is stable and the `person`/`person_photo`/`face_sample` schema is frozen.
- New tables for video (`video_job`, `video_track`, `face_video_appearance`) are designed and added via Alembic in Phase 2.
- Video workers (`worker-gpu` services) reuse the same PostgreSQL/Qdrant/MinIO platform.
- No change to the core identity schema without a new ADR.

## How to detect scope creep

| Red flag | Correct action |
|----------|----------------|
| Adding a route not in `API_CONTRACT.md` | Stop; open ADR or move to Phase 2 plan. |
| Adding a table not in `DATA_MODEL.md` | Stop; update data model and ADR first. |
| Hardcoding a model path or GPU UUID in Python | Move configuration to env/manifest. |
| Storing vectors or images in PostgreSQL | Redesign per data-ownership rules. |
| Writing a `/videos/*` placeholder | Delete; Phase 2 owns video routes. |

## Files that must not exist at Phase 1A end

- `backend/app/api/v1/videos.py`
- `backend/app/api/v1/imports.py`
- `backend/app/api/v1/faces.py`
- `backend/app/api/v1/oracle.py`
- `backend/app/api/v1/objects.py`
- `backend/app/api/v1/streams.py`
- Any migration file referencing forbidden tables.

## Open items for Phase 1B/C

- Define real-image accuracy thresholds using an internal validation set.
- Decide whether query images are retained for audit.
- Choose frontend demo scope and stack.
- Draft ADR for API key auth and future RBAC migration.

## Verification plan

- Check `docs/implementation/` contains all 12 files.
- `git status` shows no files inside `backend/` or `frontend/`.
- Grep backend plan documents for forbidden route/table names; ensure they appear only in this scope-lock document.
