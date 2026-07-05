# Task 7 — Application Services Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans / superpowers:subagent-driven-development. Steps use checkbox syntax for tracking.

**Goal:** Complete the Phase 1 application services layer for MergenVision with transaction/rollback handling, national ID hashing, and full unit test coverage.

**Architecture:** Services remain thin orchestrators over repositories and infrastructure; `FacePipeline` and `EnrollmentPipeline`/`OnlineIdentifyPipeline` stay in the adapter/application boundary. National ID hashing lives in `app.core.security` so both people creation and enrollment can reuse it. Services will propagate failures to trigger the route-level rollback in `get_db`, while performing best-effort cleanup of MinIO objects on enrollment/identification failures.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, passlib/bcrypt, pytest-asyncio.

## Global Constraints

- Phase 1 routes/tables only; no `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams`.
- Never store raw national ID, full person details, image bytes, or embeddings in Qdrant or audit.
- No TODO/TBD/FIXME markers left in code.
- UUIDv7 for new IDs via `app.core.ids.new_uuid7`.
- MinIO owns image bytes; Qdrant owns embeddings + reference payload; PostgreSQL owns business metadata.
- National ID is hashed with passlib/bcrypt and masked (`*...last4`) before persistence.

## REFERENCE_CHECK

```text
Task: Task 7 — Application Services
Phase: Phase 1
Allowed scope: backend/app/application/* service files, backend/app/core/security.py, unit tests, minimal router updates to expose selectedFaceIndex
Files allowed to change:
  - backend/app/core/security.py
  - backend/app/application/people_service.py
  - backend/app/application/photo_service.py
  - backend/app/application/enrollment_service.py
  - backend/app/application/identification_service.py
  - backend/app/application/online_identify_pipeline.py (selected_face_index support)
  - backend/app/application/audit_service.py
  - backend/app/application/stats_service.py
  - backend/app/application/readiness_service.py
  - backend/app/api/v1/identify.py (pass selectedFaceIndex)
  - backend/tests/unit/test_people_service.py
  - backend/tests/unit/test_photo_service.py
  - backend/tests/unit/test_enrollment_service.py
  - backend/tests/unit/test_identification_service.py
  - backend/tests/unit/test_stats_service.py
Files forbidden to change:
  - Routes other than identify.py
  - Repositories
  - Domain models
  - Migration files
  - Docker Compose / GPU config
Local docs checked:
  - /home/user/MergenVision/.superpowers/sdd/task-7-brief.md
  - AGENTS.md
  - docs/architecture/API_CONTRACT.md
  - docs/architecture/DATA_MODEL.md
  - docs/architecture/ARCHITECTURE_DECISION_RECORDS.md
Requirements checked:
  - requirements/phase1recognitionrequirements.md (exists, referenced)
Architecture docs checked:
  - API_CONTRACT.md
  - DATA_MODEL.md
  - ARCHITECTURE_DECISION_RECORDS.md (ADR-003, ADR-004, ADR-005, ADR-006, ADR-010, ADR-011, ADR-017, ADR-019, ADR-020)
Official docs checked via context7:
  - passlib / bcrypt hash and verify examples (Passlib readthedocs)
Open-source references checked via exa/web: None required for this task
Existing local code inspected:
  - All application service files
  - All repository files
  - app/domain/models.py
  - app/core/config.py, errors.py, ids.py, security.py
  - app/infrastructure/adapters/{pipelines.py,base.py}
  - app/infrastructure/{storage.py,vector_store.py,health_checks.py}
  - app/schemas/{people.py,photos.py,identify.py,stats.py,audit.py,health.py}
  - tests/unit/repositories/conftest.py and existing repo tests
Old lessons checked:
  - olderDiagramsProvedWrog/ — not needed for this task
Patterns to follow:
  - Repository pattern already in use; services inject repositories
  - Adapter boundary: detector/aligner/recognizer separate, FacePipeline orchestrates
  - Data ownership: embeddings never in PostgreSQL, PII never in Qdrant/audit
  - Settings-driven bucket/collection/model/version names
  - UUIDv7 for all IDs
Patterns rejected:
  - Creating new persons inside enrollment service in Phase 1 (POST /people/{id}/photos requires existing person)
  - Fake runtime pipeline in tests (use mocks)
Architecture decisions that apply:
  - ADR-003 PostgreSQL owns business metadata
  - ADR-004 Qdrant only vectors + reference payload
  - ADR-005 MinIO owns bytes
  - ADR-006 adapter boundary
  - ADR-010 UUIDv7
  - ADR-011 model/dimension/version-specific Qdrant collections
  - ADR-017 Phase 1 scope lock
  - ADR-020 face_identity known-only in Phase 1
Docker/GPU strategy that applies:
  - No GPU UUID hardcoding in application code
  - Same backend image for api/api-gpu-*
Data ownership rules that apply:
  - PostgreSQL: person, person_photo, face_identity, face_sample metadata, request/results, audit_log
  - Qdrant: vectors + reference payload only (faceId, personId, photoId, sampleId, identityType, model*, isActive)
  - MinIO: original images, face crops, query images
  - Never store raw national ID in audit/Qdrant
Security/PII rules that apply:
  - Hash national ID with bcrypt before PostgreSQL persistence
  - Mask national ID before persistence and API response
  - Audit metadata contains IDs only, no raw PII/images/embeddings
Tests/verification planned:
  - pytest tests/unit/test_*_service.py -v
  - pytest tests/unit/repositories/ -v
  - ruff check .
Unverified assumptions:
  - passlib bcrypt is installed (confirmed in pyproject.toml)
  - FastAPI route dependency `get_db` commits/rolls back the session; services flush only
  - Unit tests can mock AsyncSession, repositories, ObjectStorage, VectorStore, FacePipeline
Approval gates:
  - Plan approved before code
Out-of-scope requests detected:
  - Video/Phase 2 routes
  - Oracle import
  - Anonymous faces
  - Object detection
  - RBAC/KMS/multitenancy
  - Production sharding
  - Model training / dataset download
```

---

## Task 1: National ID hashing/masking helper

**Files:**
- Create/modify: `backend/app/core/security.py`
- Test: `backend/tests/unit/test_people_service.py` (uses helper)

**Interfaces:**
- Produces: `hash_national_id(plain: str) -> str`, `mask_national_id(plain: str | None) -> str | None`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_people_service.py` with a test that asserts PeopleService.create hashes the national ID. Run it; it fails because helper doesn't exist.

- [ ] **Step 2: Add security helper**

```python
from passlib.hash import bcrypt


def hash_national_id(national_id: str) -> str:
    return bcrypt.hash(national_id)


def mask_national_id(national_id: str | None) -> str | None:
    if national_id is None or len(national_id) < 4:
        return None
    return "*" * (len(national_id) - 4) + national_id[-4:]
```

- [ ] **Step 3: Verify PeopleService.create hashes national ID**

Update `people_service.py` to import helper, hash before duplicate check, pass hash/masked to repo.

Run: `pytest tests/unit/test_people_service.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

## Task 2: PhotoService unit tests

**Files:**
- Modify: `backend/tests/unit/test_photo_service.py` (create)
- No production changes unless bugs found

**Interfaces:**
- Consumes: PhotoRepository, FaceSampleRepository, ObjectStorage
- Produces: list_by_person, delete, get_image_url, get_crop_url

- [ ] **Step 1: Write failing tests for list/delete/URLs**

- [ ] **Step 2: Implement minimal or verify existing PhotoService passes**

Run: `pytest tests/unit/test_photo_service.py -v`
Expected: PASS

## Task 3: EnrollmentService.enroll_photo

**Files:**
- Modify: `backend/app/application/enrollment_service.py`
- Create: `backend/tests/unit/test_enrollment_service.py`

**Interfaces:**
- Consumes: EnrollmentPipeline, AuditRepository
- Produces: `EnrollResult` dataclass with person, photo, identity, sample

- [ ] **Step 1: Write failing tests**

Mock pipeline, repos, storage, vector_store. Test:
- enroll_photo calls pipeline.enroll with person_id
- audit logged with safe metadata
- EnrollResult returned
- exception triggers best-effort cleanup?

- [ ] **Step 2: Implement EnrollResult and enroll_photo**

```python
from dataclasses import dataclass

@dataclass
class EnrollResult:
    person: Person
    photo: PersonPhoto
    identity: FaceIdentity
    sample: FaceSample
```

Replace internal `_pipeline.enroll(...)` call with `enroll_photo(person_id, image_bytes)`; keep a backward-compatible `enroll(...)` wrapper for existing routes.

- [ ] **Step 3: Remove TODO, wire audit**

- [ ] **Step 4: Verify**

Run: `pytest tests/unit/test_enrollment_service.py -v`
Expected: PASS

## Task 4: IdentificationService selected_face_index

**Files:**
- Modify: `backend/app/application/identification_service.py`
- Modify: `backend/app/application/online_identify_pipeline.py`
- Modify: `backend/app/api/v1/identify.py`
- Create: `backend/tests/unit/test_identification_service.py`

**Interfaces:**
- Consumes: OnlineIdentifyPipeline, IdentificationRequestRepository, AuditRepository, ObjectStorage
- Produces: `identify(image_bytes, top_k, selected_face_index, threshold=None) -> IdentifyResponse`

- [ ] **Step 1: Write failing test for selected_face_index**

Mock pipeline to return two faces; selected_face_index=1 should result in response containing only the second face and decision `single_face`.

- [ ] **Step 2: Add selected_face_index to OnlineIdentifyPipeline**

In `identify`, after detecting faces, if `selected_face_index` is provided and valid, process only that face; otherwise process all. Map request-level decision:
- 0 faces -> "no_face"
- 1 face -> "single_face"
- >1 -> "multiple_faces"

- [ ] **Step 3: Expose selectedFaceIndex in route**

Update `identify.py` route to pass `selected_face_index=params.selectedFaceIndex`.

- [ ] **Step 4: Verify**

Run: `pytest tests/unit/test_identification_service.py -v`
Expected: PASS

## Task 5: StatsService.summary

**Files:**
- Modify: `backend/app/application/stats_service.py`
- Create: `backend/tests/unit/test_stats_service.py`

**Interfaces:**
- Produces: `summary() -> dict[str, int]`

- [ ] **Step 1: Write failing test**

- [ ] **Step 2: Rename/rename get() to summary(), keep get alias**

```python
async def summary(self) -> dict[str, int]: ...
async def get(self) -> dict[str, int]: return await self.summary()
```

- [ ] **Step 3: Verify**

Run: `pytest tests/unit/test_stats_service.py -v`
Expected: PASS

## Task 6: AuditService / ReadinessService

**Files:**
- `backend/app/application/audit_service.py`
- `backend/app/application/readiness_service.py`

- [ ] **Step 1: Confirm AuditService.list already paginated**
- [ ] **Step 2: Confirm ReadinessService.check already delegates to HealthChecks**
- [ ] **Step 3: No production changes unless bugs found**

## Task 7: Integration / verification

- [ ] **Step 1: Run all service tests**

`pytest tests/unit/test_*_service.py -v` -> PASS

- [ ] **Step 2: Run repository regression tests**

`pytest tests/unit/repositories/ -v` -> 34 passed

- [ ] **Step 3: Run ruff**

`ruff check .` -> clean

- [ ] **Step 4: Write report**

`/home/user/MergenVision/.superpowers/sdd/task-7-report.md`
