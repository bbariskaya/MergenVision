# Phase 1 TensorRT GPU Backend Rewrite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Phase 1 backend from the restored skeleton, replacing the ONNX Runtime hot path with a full-GPU TensorRT/torch stack and introducing the `face_identity` table for stable face IDs.

**Architecture:**
- FastAPI + async SQLAlchemy 2.0 + Alembic + PostgreSQL + Qdrant + MinIO.
- All image decode, detector inference, NMS, alignment, recognizer inference, and L2 normalization run on CUDA tensors.
- Only the final `[N, 512]` embedding and metadata leave the GPU.
- Offline-built TensorRT engines for static batch sizes `[1, 8, 16, 32]`; runtime selects the smallest engine ≥ actual batch and zero-pads.
- `FacePipeline` is ML-only; business services orchestrate enrollment/search/audit.

**Tech Stack:** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `httpx`, `minio`, `pillow`, `python-multipart`, `qdrant-client`, `numpy`, `torch`, `torchvision`, `tensorrt`, `cupy-cuda12x`, `nvidia-dali-cuda120`, `pytest`, `ruff`, `mypy`.

---

## Global Constraints

- API endpoint names must match `docs/architecture/API_CONTRACT.md` exactly.
- PostgreSQL tables must match `docs/architecture/DATA_MODEL.md` (`person`, `person_photo`, `face_identity`, `face_sample`, `identification_request`, `identification_query_face`, `identification_result`, `audit_log`).
- Qdrant payload is reference-only: `faceId`, `personId`, `photoId`, `sampleId`, `identityType`, `modelName`, `modelVersion`, `embeddingDimension`, `isActive`.
- No raw national ID, full person details, image bytes, base64, or embeddings stored in Qdrant payload or audit metadata.
- No hardcoded GPU UUID or physical device index in Python code.
- No `/videos/*`, `/imports/*`, `/faces/*`, `/oracle/*`, `/objects/*`, `/streams/*` routes or tables.
- No silent package installation or model download; packages are declared in `pyproject.toml` only.
- No silent git commits.
- Tests must pass on a machine without CUDA using mocks and lazy imports for `torch`, `tensorrt`, and `cupy`.

---

## File Structure (Target)

```text
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 2026_07_04_phase1_initial.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── ids.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── domain/
│   │   └── models.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── people.py
│   │   ├── photos.py
│   │   ├── identify.py
│   │   ├── audit.py
│   │   ├── stats.py
│   │   ├── media.py
│   │   └── health.py
│   ├── repositories/
│   │   ├── person_repo.py
│   │   ├── photo_repo.py
│   │   ├── face_identity_repo.py
│   │   ├── face_sample_repo.py
│   │   ├── audit_repo.py
│   │   └── identification_repo.py
│   ├── infrastructure/
│   │   ├── db.py
│   │   ├── minio_client.py
│   │   ├── qdrant_client.py
│   │   ├── storage.py
│   │   ├── vector_store.py
│   │   ├── model_registry.py
│   │   ├── health_checks.py
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── image_validator.py
│   │       ├── gpu_pil_decoder.py
│   │       ├── torch_preprocessor.py
│   │       ├── trt_session.py
│   │       ├── detector_adapter.py
│   │       ├── recognizer_adapter.py
│   │       ├── aligner_preprocessor.py
│   │       └── pipelines.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── people_service.py
│   │   ├── photo_service.py
│   │   ├── enrollment_service.py
│   │   ├── identification_service.py
│   │   ├── audit_service.py
│   │   ├── stats_service.py
│   │   └── readiness_service.py
│   └── api/
│       ├── dependencies.py
│       └── v1/
│           ├── __init__.py
│           ├── router.py
│           ├── health.py
│           ├── people.py
│           ├── photos.py
│           ├── identify.py
│           ├── identification_requests.py
│           ├── audit.py
│           ├── stats.py
│           └── media.py
├── tests/
│   ├── conftest.py
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_health_ready.py
│   │   ├── test_openapi_scope.py
│   │   ├── test_people.py
│   │   ├── test_photos.py
│   │   ├── test_identify.py
│   │   ├── test_identification_requests.py
│   │   ├── test_audit.py
│   │   └── test_stats.py
│   └── unit/
│       ├── __init__.py
│       ├── test_config.py
│       ├── test_people_service.py
│       ├── test_photo_service.py
│       ├── test_enrollment_service.py
│       ├── test_identification_service.py
│       ├── test_ids.py
│       ├── test_repositories.py
│       ├── test_storage.py
│       ├── test_image_validator.py
│       ├── test_stats_service.py
│       └── infrastructure/
│           ├── test_vector_store.py
│           ├── test_db.py
│           └── adapters/
│               ├── test_gpu_pil_decoder.py
│               ├── test_torch_preprocessor.py
│               ├── test_trt_session.py
│               ├── test_detector_adapter.py
│               ├── test_recognizer_adapter.py
│               ├── test_aligner_preprocessor.py
│               └── test_face_pipeline.py
└── scripts/
    ├── build_trt_engines.py
    └── benchmark_enrollment.py
```

---

## Task 0 — Update Governance / Source-of-Truth Docs

**Files:**
- Create: `docs/superpowers/specs/2026-07-04-phase1-tensorrt-gpu-rewrite-design.md`
- Modify: `docs/superpowers/plans/2026-07-04-phase1-tensorrt-gpu-rewrite-plan.md`
- Modify: `docs/architecture/ARCHITECTURE_DECISION_RECORDS.md` (ensure ADR-019/020/021/022 are present)
- Modify: `AGENTS.md` and `CLAUDE.md` (TensorRT no longer future-only)

**Deliverable:** Architecture docs, data model, API contract, and ADRs are internally consistent and include `face_identity` and TensorRT decisions.

- [ ] Review `API_CONTRACT.md`, `DATA_MODEL.md`, `ARCHITECTURE_DECISION_RECORDS.md`.
- [ ] Add/update ADR-019 (TensorRT/torch stack), ADR-020 (`face_identity`), ADR-021 (offline engine build), ADR-022 (CPU boundary).
- [ ] Update `AGENTS.md`/`CLAUDE.md` to remove TensorRT from future-only boundaries and add `face_identity` to allowed Phase 1 tables.

Expected: all docs open cleanly and have no `TODO`/`TBD` placeholders.

---

## Task 1 — Project Scaffolding and Dependencies

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/errors.py`
- Keep: `backend/app/core/ids.py`
- Modify: `backend/app/core/logging.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/alembic.ini`
- Modify: `backend/alembic/env.py`
- Create: `backend/app/domain/models.py`
- Test: `backend/tests/unit/test_config.py`, `backend/tests/unit/test_ids.py`

**Interfaces:**
- `Settings` populates MinIO, Qdrant, PostgreSQL, TensorRT paths, thresholds, and GPU device ID.
- `pyproject.toml` declares `torch>=2.6,<2.7`, `torchvision>=0.21,<0.22`, `tensorrt>=10.0,<11`, `cupy-cuda12x>=13.0,<14`, `nvidia-dali-cuda120>=1.0`, `alembic>=1.13,<1.15`.
- `Alembic` config points at `app.infrastructure.db:Base` and async URL.

- [ ] Step 1: Update `pyproject.toml` dependency list.
- [ ] Step 2: Add settings for `minio_url`, `minio_access_key`, `minio_secret_key`, `qdrant_url`, `qdrant_collection_prefix`, `minio_bucket_people_photos`, `minio_bucket_face_crops`, `minio_bucket_query_images`, `detector_model_path`, `recognizer_model_path`, `trt_engine_dir`, `trt_batch_profiles`, `trt_use_fp16`, `gpu_device_id`, `matched_threshold=0.6`, `possible_match_threshold=0.4`, `max_upload_bytes=10485760`.
- [ ] Step 3: Extend errors with `NoFaceDetectedError`, `MultipleFacesDetectedError`, `EngineNotFoundError`, `StorageError`.
- [ ] Step 4: Ensure `ids.new_uuid7()` is tested and used.

Run: `pytest backend/tests/unit/test_config.py backend/tests/unit/test_ids.py -v` — expected PASS.

---

## Task 2 — Database Models and Initial Migration

**Files:**
- Create: `backend/app/domain/models.py`
- Create: `backend/alembic/versions/2026_07_04_phase1_initial.py`
- Test: `backend/tests/unit/test_repositories.py`, `backend/tests/integration/test_alembic_models.py`

**Interfaces:**
- All mapped classes use `Mapped[...]` and SQLAlchemy 2.0 async style.
- Each table has `createdAt`/`updatedAt`/`isActive`/`deletedAt` as appropriate.
- `person`: `personId`, `firstName`, `lastName`, `nationalIdHash`, `nationalIdMasked`, `details`, `isActive`, `deletedAt`.
- `person_photo`: `photoId`, `personId`, `originalImageBucket`, `originalImageKey`, `contentType`, `sizeBytes`, `width`, `height`, `isActive`, `deletedAt`.
- `face_identity`: `faceId`, `identityType`, `personId`, `displayName`, `isActive`, `createdAt`, `updatedAt`.
- `face_sample`: `sampleId`, `faceId`, `photoId`, `qdrantPointId`, `collectionName`, `modelName`, `modelVersion`, `embeddingDimension`, `qualityScore`, `cropImageBucket`, `cropImageKey`, `isIndexed`, `isActive`, `deletedAt`.
- `identification_request`: `requestId`, `status`, `decision`, `faceCount`, `topK`, `threshold`, `queryImageBucket`, `queryImageKey`, `completedAt`, `errorMessage`.
- `identification_query_face`: `queryFaceId`, `requestId`, `boundingBox`, `landmarks`, `qualityScore`.
- `identification_result`: `resultId`, `requestId`, `queryFaceId`, `faceId`, `sampleId`, `personId`, `score`, `rank`, `decision`.
- `audit_log`: `auditId`, `action`, `entityType`, `entityId`, `actor`, `requestId`, `outcome`, `safeMetadata`.

- [ ] Step 1: Write failing import test for `Person` model.
- [ ] Step 2: Implement models with correct types, FKs, indexes.
- [ ] Step 3: Generate Alembic initial migration (or hand-write) that creates all Phase 1 tables.
- [ ] Step 4: Run repository/migration tests.

Run: `pytest backend/tests/unit/test_repositories.py backend/tests/integration/test_alembic_models.py -v` — expected PASS.

---

## Task 3 — Pydantic Schemas

**Files:**
- Create/modify: `backend/app/schemas/common.py`, `people.py`, `photos.py`, `identify.py`, `audit.py`, `stats.py`, `media.py`, `health.py`
- Test: `backend/tests/unit/test_schemas.py` (optional)

**Interfaces:**
- `PersonCreate`, `PersonUpdate`, `PersonResponse`, `PersonListResponse`.
- `PhotoEnrolledResponse`, `PhotoListResponse`, `PhotoResponse`.
- `IdentifyRequest` (multipart via router, schema only documents the response), `IdentifyResponse`, `IdentifyFaceResult`, `Candidate`.
- `IdentificationRequestSummary`, `IdentificationRequestListResponse`.
- `AuditEntry`, `AuditListResponse`.
- `StatsResponse`.
- `common.ListingResponse[T]` generic.
- `health.HealthResponse`, `ready.ReadyResponse`.

- [ ] Step 1: Add schemas matching API_CONTRACT response examples.
- [ ] Step 2: Add helper validators (e.g. nationalId length must be 11 digits in Turkey mode) where useful.
- [ ] Step 3: Run schema serialization tests.

Run: `pytest backend/tests/unit/test_schemas.py -v` — expected PASS.

---

## Task 4 — Infrastructure Clients

**Files:**
- Create/modify:
  - `backend/app/infrastructure/minio_client.py`
  - `backend/app/infrastructure/qdrant_client.py`
  - `backend/app/infrastructure/storage.py`
  - `backend/app/infrastructure/vector_store.py`
  - `backend/app/infrastructure/model_registry.py`
  - `backend/app/infrastructure/health_checks.py`
- Test: `backend/tests/unit/infrastructure/test_storage.py`, `test_vector_store.py`

**Interfaces:**
- `get_minio_client()` returns `Minio`.
- `get_qdrant_client()` returns `AsyncQdrantClient`.
- `ObjectStorage`: `upload(bucket, key, data, content_type)`, `get_object(bucket, key)`, `delete(bucket, key)`, `presigned_get_url(bucket, key, expires=3600)`.
- `VectorStore`: `collection_name(model_name, dimension, version)`, `ensure_collection(...)`, `upsert_batch(points)`, `search(embedding, top_k, filter)`.
- `ModelRegistry`: returns detector/recognizer info (`local_path`, `name`, `version`, `input_shape`, `output_dim`).
- `HealthChecks`: async `check_postgres()`, `check_qdrant()`, `check_minio()`, `check_runtime()`.

- [ ] Step 1: Implement `ObjectStorage` with explicit bucket creation attempts and clear error messages.
- [ ] Step 2: Implement `VectorStore` with cosine distance and required payload indexes (`faceId`, `personId`, `photoId`, `identityType`, `isActive`).
- [ ] Step 3: Implement `ModelRegistry` reading from `Settings`.
- [ ] Step 4: Implement `HealthChecks` returning booleans (no exceptions leak).

Run: `pytest backend/tests/unit/infrastructure/test_storage.py backend/tests/unit/infrastructure/test_vector_store.py -v` — expected PASS.

---

## Task 5 — GPU Adapter Primitives and Pipeline

**Files:**
- Create:
  - `backend/app/infrastructure/adapters/base.py`
  - `backend/app/infrastructure/adapters/image_validator.py`
  - `backend/app/infrastructure/adapters/gpu_pil_decoder.py`
  - `backend/app/infrastructure/adapters/torch_preprocessor.py`
  - `backend/app/infrastructure/adapters/trt_session.py`
  - `backend/app/infrastructure/adapters/detector_adapter.py`
  - `backend/app/infrastructure/adapters/recognizer_adapter.py`
  - `backend/app/infrastructure/adapters/aligner_preprocessor.py`
  - `backend/app/infrastructure/adapters/pipelines.py`
- Test:
  - `backend/tests/unit/infrastructure/adapters/test_gpu_pil_decoder.py`
  - `test_torch_preprocessor.py`
  - `test_trt_session.py`
  - `test_detector_adapter.py`
  - `test_recognizer_adapter.py`
  - `test_aligner_preprocessor.py`
  - `test_face_pipeline.py`

**Interfaces:**
- `Detection(NamedTuple)`: `image_index`, `bbox`, `score`, `landmarks`.
- `DetectionBatch`: iterable; `by_image` grouping.
- `EmbeddingBatch`: `embeddings: np.ndarray`, model metadata, `dimension`.
- `GpuPilDecoder.decode_batch(image_bytes_list) -> torch.Tensor`: uses Pillow (CPU) because stable nvJPEG Python bindings are not available; keeps tensors on `input_tensor.device` after decode/permute.
- `TorchPreprocessor.resize_normalize(images, size, mean, std) -> torch.Tensor`.
- `TrtInferenceSession.infer(input_tensor) -> list[np.ndarray]` uses TensorRT CUDA bindings.
- `DetectorAdapter.from_registry()` selects engine file for batch size; `detect_batch(images) -> DetectionBatch` (torch-based SCRFD decode + `torchvision.ops.nms`).
- `AlignerPreprocessor.align_crops(images, detections) -> torch.Tensor` using 5-landmark affine grid sample.
- `RecognizerAdapter.embed_batch(crops) -> EmbeddingBatch` L2-normalized.
- `FacePipeline.enroll(image_bytes) -> EnrollOutput`; `identify_prepare(image_bytes) -> list[QueryFaceOutput]`; raises `NoFaceDetectedError` / `MultipleFacesDetectedError` for enrollment.

- [ ] Step 1: Implement `base.py`, `image_validator.py`, and lazy-loading primitives.
- [ ] Step 2: Write test for `DetectorAdapter` with mocked TensorRT outputs matching the SCRFD 9-output order.
- [ ] Step 3: Implement torch-based SCRFD decoder (translate the numpy implementation in the old adapter to torch; use `torchvision.ops.nms`).
- [ ] Step 4: Implement recognizer and aligner.
- [ ] Step 5: Implement `FacePipeline` orchestration and encode face crop JPEG.
- [ ] Step 6: Run adapter/pipeline unit tests with mocks.

Run: `pytest backend/tests/unit/infrastructure/adapters/ -v` — expected PASS.

---

## Task 5.5 — DALI Decoder, BatchEnrollmentPipeline, and Async Bulk Persistence

**Files:**
- Create/modify:
  - `backend/app/infrastructure/adapters/gpu_dali_decoder.py`
  - `backend/app/infrastructure/adapters/batch_enrollment_pipeline.py`
  - Modify `backend/app/infrastructure/adapters/pipelines.py` for batch `enroll_batch`
  - Modify `backend/app/infrastructure/adapters/base.py` with batch-friendly outputs
  - Modify `backend/app/repositories/face_sample_repo.py` with `bulk_create`
  - Modify `backend/app/repositories/photo_repo.py` with `bulk_create`
  - Modify `backend/app/repositories/face_identity_repo.py` with `bulk_create_known`
  - Modify `backend/app/infrastructure/vector_store.py` with `upsert_batch` accepting 100–1000 points
  - Modify `backend/app/infrastructure/storage.py` with async concurrent upload helper
  - Modify `backend/app/application/enrollment_service.py` to orchestrate batch persistence
- Test:
  - `backend/tests/unit/infrastructure/adapters/test_gpu_dali_decoder.py`
  - `backend/tests/unit/infrastructure/adapters/test_batch_enrollment_pipeline.py`
  - `backend/tests/unit/test_enrollment_service.py` (update)

**Interfaces:**
- `GpuDaliDecoder.decode_batch(image_bytes_list) -> tuple[torch.Tensor, torch.Tensor]`: first tensor is original decoded `[N,3,H,W]`, second is detector-ready `[N,3,size,size]`. Lazy imports `nvidia.dali`; raises `RuntimeError` if DALI unavailable so callers fall back to `GpuPilDecoder` + `TorchPreprocessor`.
- `FacePipeline.enroll_batch(image_bytes_list) -> list[list[EnrollOutput]]`: uses static batch profile `[1,8,16,32]`, packs each chunk into the smallest fitting profile, zero-pads, and runs detector/recognizer in batch. Falls back to single-image PIL path when DALI unavailable or batch size is 1 on CPU.
- `BatchEnrollmentPipeline.enroll_batch(person_id, image_bytes_iterable) -> EnrollBatchResult`: orchestrates decode → detect/align/recognize in packed batches → async bulk persistence:
  - PostgreSQL batch insert for `person_photo` and `face_sample` rows (`insert(...).values([...])`).
  - Qdrant batch upsert in 100–1000 point chunks.
  - MinIO concurrent upload of originals + crops via `asyncio.gather`.
- `ObjectStorage.upload_concurrent(items: list[UploadItem]) -> list[str]`: runs object store uploads concurrently.
- `VectorStore.upsert_batch(points: list[PointStruct], batch_size: int = 500) -> None`.
- `FaceSampleRepository.bulk_create(samples: list[FaceSample])` and similar for photo/identity.
- CPU-only tests mock DALI and TensorRT; PIL fallback path is always exercised.

- [ ] Step 1: Implement `GpuDaliDecoder` with lazy DALI import, per-batch pipeline caching, and DLPack-to-torch conversion.
- [ ] Step 2: Add `FacePipeline.enroll_batch` using `[1,8,16,32]` packed batches.
- [ ] Step 3: Add repository bulk create methods.
- [ ] Step 4: Add `VectorStore.upsert_batch` and `ObjectStorage.upload_concurrent`.
- [ ] Step 5: Implement `BatchEnrollmentPipeline` with decode/inference/io lane separation.
- [ ] Step 6: Update `EnrollmentService` to expose single-photo entry point (existing API) delegating to batch pipeline for lists, and a direct batch entry point for the benchmark script.
- [ ] Step 7: Write unit tests for DALI decoder (mocked), batch enrollment pipeline, and bulk persistence.

Run: `pytest backend/tests/unit/infrastructure/adapters/test_gpu_dali_decoder.py backend/tests/unit/infrastructure/adapters/test_batch_enrollment_pipeline.py backend/tests/unit/test_enrollment_service.py -v` — expected PASS.

---

## Task 6 — Repositories

**Files:**
- Create/modify:
  - `backend/app/repositories/person_repo.py`
  - `backend/app/repositories/photo_repo.py`
  - `backend/app/repositories/face_identity_repo.py`
  - `backend/app/repositories/face_sample_repo.py`
  - `backend/app/repositories/audit_repo.py`
  - `backend/app/repositories/identification_repo.py`
- Test: `backend/tests/unit/repositories/test_*.py`

**Interfaces:**
- Each repo accepts `AsyncSession` in constructor and exposes async CRUD methods.
- `PersonRepository`: `create(...)`, `get_by_id`, `list_active`, `update`, `soft_delete`, `exists_by_national_id_hash`.
- `PhotoRepository`: `create`, `list_active_by_person`, `get_by_id`, `soft_delete`.
- `FaceIdentityRepository`: `create_known`, `get_by_id`, `list_active_by_person`, `soft_delete`.
- `FaceSampleRepository`: `create`, `mark_indexed`, `soft_delete_by_photo`, `list_active_by_person`.
- `AuditRepository`: `log`, `list_filtered`.
- `IdentificationRequestRepository`: `create`, `add_query_faces`, `add_results`, `complete`, `get_by_id`, `list`.

- [ ] Step 1: Implement repositories.
- [ ] Step 2: Write unit tests using in-memory SQLite (`aiosqlite`) via `create_async_engine("sqlite+aiosqlite:///:memory:")`.
- [ ] Step 3: Run repository tests.

Run: `pytest backend/tests/unit/repositories/ -v` — expected PASS.

---

## Task 7 — Application Services

**Files:**
- Create/modify:
  - `backend/app/application/people_service.py`
  - `backend/app/application/photo_service.py`
  - `backend/app/application/enrollment_service.py`
  - `backend/app/application/identification_service.py`
  - `backend/app/application/audit_service.py`
  - `backend/app/application/stats_service.py`
  - `backend/app/application/readiness_service.py`
- Test:
  - `backend/tests/unit/test_people_service.py`
  - `backend/tests/unit/test_photo_service.py`
  - `backend/tests/unit/test_enrollment_service.py`
  - `backend/tests/unit/test_identification_service.py`
  - `backend/tests/unit/test_stats_service.py`

**Interfaces:**
- `PeopleService`: create/list/get/update/soft-delete person; hash/mask national ID via HMAC-SHA256 with a server-side pepper.
- `EnrollmentService.enroll_photo(person_id, image_bytes) -> EnrollResult` runs validation, `FacePipeline.enroll`, uploads original + crop to MinIO, inserts `face_identity`, `person_photo`, `face_sample`, Qdrant upsert, marks indexed, audits.
- `IdentificationService.identify(image_bytes, top_k, selected_face_index) -> IdentifyResult` stores query image if configured, detects faces, searches Qdrant per face, records request/query/results, returns candidates and decision.
- `AuditService.list(...)` paginated.
- `StatsService.summary()` returns counts.
- `ReadinessService.check()` uses `HealthChecks`.

- [ ] Step 1: Implement services with explicit transaction boundaries and rollback handling.
- [ ] Step 2: Add unit tests mocking repositories, storage, vector store, and FacePipeline.
- [ ] Step 3: Run service tests.

Run: `pytest backend/tests/unit/test_*_service.py -v` — expected PASS.

---

## Task 8 — API Routers and Dependencies

**Files:**
- Create/modify:
  - `backend/app/api/dependencies.py`
  - `backend/app/api/v1/router.py`
  - `backend/app/api/v1/health.py`
  - `backend/app/api/v1/people.py`
  - `backend/app/api/v1/photos.py`
  - `backend/app/api/v1/identify.py`
  - `backend/app/api/v1/identification_requests.py`
  - `backend/app/api/v1/audit.py`
  - `backend/app/api/v1/stats.py`
  - `backend/app/api/v1/media.py`
- Test:
  - `backend/tests/api/test_health_ready.py`
  - `backend/tests/api/test_openapi_scope.py`
  - `backend/tests/api/test_people.py`
  - `backend/tests/api/test_photos.py`
  - `backend/tests/api/test_identify.py`
  - `backend/tests/api/test_identification_requests.py`
  - `backend/tests/api/test_audit.py`
  - `backend/tests/api/test_stats.py`

**Interfaces:**
- `dependencies.py`: `get_db_session`, `get_people_service`, `get_photo_service`, `get_enrollment_service`, `get_identification_service`, `get_audit_service`, `get_stats_service`, `get_readiness_service`, and lazy `get_face_pipeline`/`get_vector_store`.
- All Phase 1 endpoints per `API_CONTRACT.md`.
- `/media/{bucket}/{objectKey}` returns a redirect to a presigned URL.
- Exception handlers map `MergenVisionError` to the status in `ERROR_STATUS_MAP`.

- [ ] Step 1: Implement dependencies and routers.
- [ ] Step 2: Add exception handlers in `main.py`.
- [ ] Step 3: Run API tests with mocked services.

Run: `pytest backend/tests/api/ -v` — expected PASS.

---

## Task 9 — Lifespan, Main Wiring, and Readiness

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/dependencies.py`
- Modify: `backend/app/application/readiness_service.py`
- Modify: `backend/app/infrastructure/health_checks.py`
- Test: `backend/tests/api/test_health_ready.py`

**Interfaces:**
- `lifespan` creates/closes long-lived clients and pre-loads `FacePipeline` lazily on first request.
- `/ready` checks PostgreSQL, Qdrant, MinIO, and TensorRT runtime loaded status.

- [ ] Step 1: Wire lifespan and startup checks.
- [ ] Step 2: Ensure `/ready` returns `503` if a dependency is down.
- [ ] Step 3: Run health/ready tests.

Run: `pytest backend/tests/api/test_health_ready.py -v` — expected PASS.

---

## Task 10 — Scripts

**Files:**
- Create:
  - `backend/scripts/build_trt_engines.py`
  - `backend/scripts/benchmark_enrollment.py`
- Test:
  - `backend/tests/scripts/test_build_trt_engines.py`

**Interfaces:**
- `build_trt_engines.py --models-dir <dir> --output-dir <dir> --batch-sizes 1 8 16 32 --fp16` builds `*.onnx_batch_{N}.plan` files for detector and recognizer.
- `benchmark_enrollment.py --dataset <path> --output benchmark.json` runs only if `tensorrt`/`torch`/`nvidia.dali` are importable and a CUDA device is present; otherwise skips with a clear message. It uses `BatchEnrollmentPipeline` with the `[1,8,16,32]` batch profile, async bulk persistence, and reports throughput (img/s) and total time.

- [ ] Step 1: Implement offline TensorRT engine builder with explicit missing-environment error.
- [ ] Step 2: Implement LFW throughput benchmark script.
- [ ] Step 3: Add unit test that mocks the TensorRT builder network calls.

Run: `pytest backend/tests/scripts/test_build_trt_engines.py -v` — expected PASS.

---

## Task 11 — Final Verification

**Files:** all deliverables.

- [ ] Step 1: Run full test suite.

Run: `cd backend && pytest -q`
Expected: PASS.

- [ ] Step 2: Run lint and type check.

Run:
```bash
cd backend && ruff check .
cd backend && ruff format --check .
cd backend && mypy .
```
Expected: all clean.

- [ ] Step 3: Grep checks.

Run:
```bash
cd backend && grep -R "videos/\|imports/\|faces/\|oracle/\|objects/\|streams/" app/api || true
cd backend && grep -R "UUID.*GPU\|CUDA_VISIBLE_DEVICES\|nvidia.com" app || true
```
Expected: no forbidden route prefixes; no GPU UUID hardcoding.

- [ ] Step 4: Report `git status`, `git diff --stat`, and unverified assumptions.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-04-phase1-tensorrt-gpu-rewrite-plan.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per major task, review between tasks.
2. **Inline Execution** — execute tasks in this session using `superpowers:executing-plans`.

Use `superpowers:subagent-driven-development` if subagents are available.
