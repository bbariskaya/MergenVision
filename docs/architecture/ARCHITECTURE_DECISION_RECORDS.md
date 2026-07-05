# MergenVision — Architecture Decision Records

## ADR-001 Root-Level REST API

**Decision:** Use root-level REST endpoints (`/people`, `/identify`) rather than nested `/v1/faces` style.

**Rationale:** Domain clarity and easier long-term versioning across photo/video/live phases.

## ADR-002 Shared Data Platform

**Decision:** PostgreSQL + Qdrant + MinIO form a single shared platform used by Phase 1 API and future Phase 2/3 workers.

**Rationale:** Avoid separate stacks; add domain-specific tables/collections/buckets per phase.

## ADR-003 PostgreSQL as Business Metadata Source of Truth

**Decision:** PostgreSQL is the source of truth for person identity, photo/sample metadata, request history, audit logs, and future video job metadata.

**Rationale:** ACID, queryable, well-understood.

## ADR-004 Qdrant as Vector Index Only

**Decision:** Qdrant stores only embeddings and a reference payload. No PII or image bytes.

**Rationale:** Privacy and separation of concerns.

## ADR-005 MinIO as Object Storage

**Decision:** MinIO stores all image/video byte data.

**Rationale:** Cheap object storage; scalable; avoids bloating PostgreSQL.

## ADR-006 Detector/Aligner/Recognizer Adapter Boundary

**Decision:** Detector, alignment, and recognizer are separate adapter boundaries orchestrated by `FacePipeline`.

**Rationale:** Allows independent model swaps and easier testing.

## ADR-007 One API Replica per Physical GPU

**Decision:** In GPU demo mode each `api-gpu-*` container is pinned to one physical GPU and sees it as `cuda:0`.

**Rationale:** Removes GPU index assumptions from Python code.

## ADR-010 UUIDv7

**Decision:** Use UUIDv7 for all primary keys.

**Rationale:** Time-sortable, shard-friendly, no national ID exposure.

## ADR-011 Model/Dimension/Version-Specific Qdrant Collections

**Decision:** Create a Qdrant collection per `(modelName, embeddingDimension, modelVersion)` tuple.

**Rationale:** Prevents mixing incompatible embeddings; makes model migration explicit.

## ADR-012 No Fake Runtime Pipeline

**Decision:** Runtime pipeline must use real model inference. Tests use mocks.

**Rationale:** Avoid drift between demo and production behavior.

## ADR-017 Phase 1 Scope Lock

**Decision:** Phase 1 exposes only `/people`, `/identify`, `/identification-requests`, `/audit`, `/stats`, `/media` and allowed Phase 1 tables. No future routes/tables.

**Rationale:** Deliver working platform before expanding.

## ADR-019 TensorRT/Torch GPU-Only Phase 1 Stack

**Status:** Approved.

**Decision:** Phase 1 hot path uses `torch`, `torchvision`, `tensorrt`, and `cupy`. ONNX Runtime CUDAExecutionProvider is removed from the hot path.

**Rationale:** Highest throughput for enrollment and identification; offline-built TensorRT engines minimize cold-start overhead.

**Consequences:**
- Engine files are GPU/architecture-specific; build script committed, engine files not committed.
- Tests must mock `tensorrt`/`torch`/`cupy` to run on CPU-only CI.
- TensorRT engine build requires matching CUDA/cuDNN/TensorRT environment.

## ADR-020 Stable Face Identity (`face_identity`)

**Status:** Approved.

**Decision:** Introduce `face_identity` table in Phase 1 to provide a stable face-level UUID across photo, video, and live phases. `identityType='known'` in Phase 1; `identityType='anonymous'` added in Phase 2.

**Rationale:** Phase 2 requirement explicitly requires a persistent `faceId` for every tracked face, stable across videos. Per-sample IDs would create multiple IDs per person, breaking video aggregation.

**Consequences:**
- `face_sample` references `face_identity.faceId` instead of `personId` directly.
- `identification_result` references both `faceId` and `sampleId`.
- Qdrant payload includes `faceId` and `identityType`.
- `anonymous_face` table is superseded by `face_identity.identityType='anonymous'`.

## ADR-021 Offline TensorRT Engine Build

**Decision:** Build TensorRT engines offline for a fixed set of static batch sizes `[1, 8, 16, 32]`. Runtime selects the smallest engine size ≥ actual batch and zero-pads.

**Rationale:** Fast cold start, deterministic shapes, avoids runtime compilation complexity.

## ADR-022 CPU Boundary at Final Embedding

**Decision:** The only CPU crossing on the hot path is the final `[N,512]` embedding and metadata. All prior steps run in CUDA tensors.

**Rationale:** Minimizes PCIe transfer and Python overhead.
