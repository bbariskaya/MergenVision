# No-Scope-Creep Rules

> **Status:** Accepted  
> **Scope:** Phase 1 implementation and any intermediate phase.

This document lists the items that are explicitly forbidden in Phase 1. If a request includes any of these, stop and escalate.

## Forbidden Phase 1 Runtime Routes

The following routes must not exist in Phase 1 runtime code:

```text
/videos/*
/imports/*
/faces/*
/oracle/*
/objects/*
/streams/*
```

Also forbidden:

- Any `501 Not Implemented` placeholder route for future APIs.
- Any empty router for future APIs.
- Any OpenAPI schema exposure for future endpoints.
- Any route that does not appear in `docs/architecture/API_CONTRACT.md`.

## Forbidden Phase 1 Database Tables

The following tables must not be created in Phase 1 migrations or runtime code:

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

Phase 1 allowed tables are only:

```text
person
person_photo
face_sample
identification_request
identification_query_face
identification_result
audit_log
```

## Forbidden Phase 1 Implementations

Do not implement any of the following in Phase 1:

- Oracle database import or synchronization.
- `/imports/*` endpoints or async batch importer workers.
- Video upload, processing, streaming, or RTSP ingestion.
- Object detection unrelated to face recognition.
- TensorRT optimization.
- Production RBAC/KMS/multitenancy.
- Production sharding for 10M+ records.
- Anonymous face identity model.
- LFW benchmark pipeline (unless explicitly in a Phase 0B/1 model verification task).
- Generic multi-model gallery switching UI.
- Real-time dashboard for live camera streams.

## Forbidden Code Patterns

Do not write:

- Fake runtime `FacePipeline` that returns hardcoded or random embeddings.
- Placeholder future routes with `TODO` or `pass`.
- Empty routers mounted at `/videos`, `/imports`, `/faces`, etc.
- Business schema that depends specifically on SCRFD or ArcFace (use adapter boundary instead).
- Hardcoded model paths in business logic.
- Qdrant collection names without model/dimension/version logic.
- Code that contradicts any accepted ADR.

## Forbidden Operational Actions

Do not perform any of the following without explicit approval:

- Install new packages.
- Download models or datasets.
- Create Docker Compose files in governance-only phases.
- Create migration files in governance-only phases.
- Create backend or frontend folders in governance-only phases.
- Commit, push, or open pull requests.

## Future Boundaries

The following remain future until explicitly approved:

| Feature | Planned phase / status |
|---|---|
| Oracle import | Future; not Phase 1 |
| Video processing | Phase 2 |
| Object detection | Future; not Phase 1 |
| TensorRT | Future |
| 10M+ production sharding | Future |
| RBAC / KMS / multitenancy | Future |
| Anonymous face identity | Phase 2 / open question |

## Escalation Rule

When a forbidden item is requested:

1. Do not implement it.
2. Record it in `REFERENCE_CHECK` under `Out-of-scope requests detected:`.
3. Record it in the final report.
4. Ask the user whether to:
   - keep it out of scope,
   - move it to Phase 2 planning, or
   - create a formal ADR and approval gate for an exception.

## Allowed Mentions

Architecture docs, requirements documents, and governance docs may mention forbidden routes/tables for planning purposes. Runtime code, migrations, and tests (except tests explicitly verifying rejection of future routes) must not implement them.
