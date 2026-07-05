# Phase Implementation Gates

> **Status:** Accepted  
> **Scope:** All future MergenVision phases.

Every future phase must pass through a gate before work begins. This document defines the gates and stop conditions.

## Gate Template

Each gate requires:

1. Entry criteria — what must be true before entering.
2. Activities — what is done during the gate.
3. Exit criteria / deliverables — what must be produced to leave the gate.
4. Stop conditions — reasons to halt and ask for direction.

## Phase 0B — Model Verification Gate

**Purpose:** Verify candidate models before any application code is written.

**Entry criteria:**

- Phase 0 architecture docs are complete and internally consistent.
- `docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md` and `MODEL_MANIFEST.json` exist.
- Candidate models are present locally or clearly marked as blocked.

**Activities:**

- Load `scrfd_10g_320_batch.onnx` and `arcface_w600k_r50_batch.onnx` with ONNX Runtime.
- Confirm input/output shapes and dynamic-axes behavior.
- Confirm CUDAExecutionProvider availability if GPU demo is targeted.
- Test single-image and small-batch inference.
- Record actual `modelName`, `modelVersion`, `embeddingDimension`, and provider behavior.
- Update `MODEL_MANIFEST.json` with `verified_locally: true/false`.

**Exit criteria:**

- A written model verification report (can be appended to `PHASE_0A_MODEL_ACCESS_REPORT.md` or a new `PHASE_0B_MODEL_VERIFICATION_REPORT.md`).
- Known shapes and known limitations.
- Decision to proceed with SCRFD+ArcFace, fallback to YuNet/SFace, or block until replacement is found.

**Stop conditions:**

- Model files are missing or corrupt.
- Output shapes do not match architecture assumptions.
- CUDA provider fails in the intended environment.
- Batch behavior is inconsistent or leaks state between inputs.
- License/product risk cannot be accepted.

## Phase 1 — Implementation Plan Gate

**Purpose:** Plan the exact Phase 1 implementation before writing code.

**Entry criteria:**

- Phase 0B model verification passed or explicitly accepted with documented risk.
- Architecture docs are approved by the product owner.
- `AGENTS.md`, `CLAUDE.md`, and governance docs are in place.

**Activities:**

- Write an implementation plan covering:
  - target directory layout
  - exact files to create/modify
  - package dependencies and versions
  - migration plan
  - test plan
  - Docker Compose scope (dev/simple first; GPU demo later)
  - risks and unverified assumptions
  - rollback plan
- Produce `REFERENCE_CHECK` for the whole plan.
- Get approval before proceeding.

**Exit criteria:**

- Approved implementation plan stored in `docs/architecture/PHASE1_IMPLEMENTATION_PLAN.md`.
- Exact task list created.
- No forbidden routes/tables in the plan.

**Stop conditions:**

- Plan includes `/videos/*`, `/imports/*`, `/faces/*`, etc.
- Plan includes forbidden tables.
- Plan relies on unverified model behavior as a business assumption.
- Plan introduces packages/models without approval.

## Phase 1 — Skeleton Gate

**Purpose:** Create the minimal project skeleton (no business logic, no inference, no migrations).

**Entry criteria:**

- Implementation plan approved.

**Activities:**

- Create backend folder structure following the plan.
- Create FastAPI app shell with `/health` and `/ready` routes only.
- Add dependency/config placeholders.
- Add skeleton tests that assert `/health` returns 200.
- Run lint/typecheck/tests.

**Exit criteria:**

- App starts and `/health` responds.
- Tests pass.
- No business endpoints, no database models, no inference code added yet.

**Stop conditions:**

- Business endpoints like `/people` or `/identify` are implemented before skeleton verification.
- Placeholder future routes are added.

## Phase 1 — Vertical Slice Gates

Phase 1 is delivered as small vertical slices. Each slice has its own mini-gate.

### Slice 1 — Person CRUD

- `POST /people`
- `GET /people`
- `GET /people/{personId}`
- `PATCH /people/{personId}`
- `DELETE /people/{personId}`

### Slice 2 — Photo Enrollment Metadata

- `POST /people/{personId}/photos`
- `GET /people/{personId}/photos`
- `DELETE /people/{personId}/photos/{photoId}`
- MinIO object upload/download pattern.

### Slice 3 — Face Sample & Qdrant Enrollment

- Face detection/alignment/recognition adapter wiring.
- `face_sample` table + Qdrant upsert.
- Model metadata tracking.

### Slice 4 — Identify & Identification History

- `POST /identify`
- `GET /identification-requests`
- `GET /identification-requests/{requestId}`
- Result enrichment.

### Slice 5 — Audit & Stats

- `GET /audit`
- `GET /stats`

### Slice 6 — Media Access

- `GET /media/{bucket}/{objectKey}`

For each slice:

- Produce a `REFERENCE_CHECK`.
- Write tests before or alongside implementation.
- Verify slice independently before moving on.
- Update the implementation plan if assumptions change.

## Phase 2 — Future Gate

**Purpose:** Plan Phase 2 only after Phase 1 is complete and stable.

**Entry criteria:**

- Phase 1 is feature-complete and all tests pass.
- Phase 1 has been used in at least one internal smoke test.
- Anonymous face identity, video pipeline, and worker topology questions are answered.

**Activities:**

- Update `API_CONTRACT.md` with Phase 2 routes (e.g., `/videos/*` and `/faces/*`).
- Update `DATA_MODEL.md` with Phase 2 tables (e.g., `video_job`, `face_identity`).
- Update `RUNTIME_TOPOLOGY.md` with `worker-gpu` services.
- Produce a new implementation plan for video upload, job queue, and worker processing.

**Exit criteria:**

- Phase 2 plan approved.
- Architecture docs updated.
- Shared identity platform constraints preserved.

**Stop conditions:**

- Phase 2 features are requested before Phase 1 is complete.
- Phase 2 design attempts to create a separate permanent data platform.

## General Stop Conditions

Stop and ask for direction when any of the following happen:

- Scope is ambiguous.
- A forbidden route or table is requested.
- A previous ADR needs to be changed.
- A required tool is unavailable and no acceptable fallback exists.
- Verification fails and the fix is not trivial.
- The user asks for code changes that contradict this governance.

## Approval Chain

| Gate | Who can approve |
|---|---|
| Phase 0B completion | Product owner / technical lead |
| Phase 1 implementation plan | Product owner / technical lead |
| Phase 1 skeleton | Self within plan, then report |
| Phase 1 vertical slices | Self within plan, then report |
| Phase 2 planning | Product owner / technical lead |
