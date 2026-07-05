# Phase 1 TensorRT GPU Backend Rewrite — Design Specification

## Goal

Deliver the complete Phase 1 backend for MergenVision using a full-GPU inference hot path (`torch`, `torchvision`, `tensorrt`, `nvidia.dali`) while preserving the root-level API contract, the PostgreSQL/Qdrant/MinIO data-ownership boundary, and Phase 1 scope lock.

## Architecture

- The backend is a FastAPI application layered as: API → Application Services → Repositories → SQLAlchemy models + MinIO/Qdrant clients.
- ML inference is isolated behind the adapter boundary: `ImageValidator`, `DetectorAdapter`, `AlignerPreprocessor`, `RecognizerAdapter`, `FacePipeline`, `GpuDaliDecoder`, `GpuPilDecoder`, `BatchEnrollmentPipeline`.
- JPEG decode runs on GPU when `nvidia.dali` is available (`fn.decoders.image(device="mixed")`) and falls back to Pillow (`GpuPilDecoder`) on CPU-only hosts. After decode, resize, detector inference, NMS, alignment, recognizer inference, and L2 normalization remain on GPU.
- Only the final `[N, 512]` embedding and metadata cross to CPU; bytes are stored in MinIO and records in PostgreSQL; vectors are indexed in Qdrant.
- TensorRT engines are built offline for static batch sizes `[1, 8, 16, 32]`; at runtime the smallest engine size ≥ actual batch is selected and the batch is zero-padded.
- `BatchEnrollmentPipeline` processes variable-size image batches using the smallest profile that fits, executes GPU inference in packed batches, and persists results with bulk PostgreSQL inserts, Qdrant batch upserts, and concurrent MinIO uploads.
- Engine files are GPU/architecture-specific and are not committed; the build script is committed.
- Python code never hardcodes a GPU UUID or physical GPU index; device selection is driven by `gpu_device_id` config.

## Phase 1 Scope Lock

- Routes: only `/health`, `/ready`, `/people`, `/people/{personId}/photos`, `/identify`, `/identification-requests`, `/audit`, `/stats`, `/media`.
- Tables: `person`, `person_photo`, `face_identity`, `face_sample`, `identification_request`, `identification_query_face`, `identification_result`, `audit_log`.
- `face_identity` is introduced now with `identityType = known` so that Phase 2/3 can reuse a stable `faceId`.
- No `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams` routes or Phase 2 tables.

## Data Ownership

- PostgreSQL: person/face metadata, photo/sample metadata, identification request history/results, audit logs.
- Qdrant: embeddings plus reference-only payload (`faceId`, `personId`, `photoId`, `sampleId`, `identityType`, `modelName`, `modelVersion`, `embeddingDimension`, `isActive`).
- MinIO: original images, face crops, query images if retained.

Never store in Qdrant or audit: raw national ID, full person details, image bytes/base64, embeddings.
Never store in PostgreSQL: raw embedding vectors, image bytes.

## Model Adapter Boundary

- `ImageValidator`: checks MIME type, dimensions, file size.
- `GpuDaliDecoder`: decodes JPEG bytes on GPU via `nvidia.dali`, resizing and normalizing to detector input; returns both the original decoded tensor and the model-input tensor as torch CUDA tensors. Falls back to `RuntimeError` so callers can use `GpuPilDecoder` when DALI is unavailable.
- `GpuPilDecoder`: decodes JPEG/PNG bytes into `[N, 3, H, W]` RGB torch tensors using Pillow; keeps tensors on the configured device.
- `TorchPreprocessor`: resizes and normalizes a tensor batch for detector input.
- `DetectorAdapter`: loads the TensorRT detector engine and outputs `DetectionBatch`.
- `AlignerPreprocessor`: converts detected faces to `[M, 3, 112, 112]` crops using a 5-point landmark template.
- `RecognizerAdapter`: loads the TensorRT recognizer engine and outputs L2-normalized `[M, 512]` embeddings.
- `FacePipeline`: orchestrates decode → detect → align → recognize; returns enrollment or identification outputs for a single image or a batch.
- `BatchEnrollmentPipeline`: high-throughput batch enrollment using GPU decode, packed batch inference (`[1,8,16,32]` profiles), and async bulk persistence.

## Person Schema

- `firstName`, `lastName`, `nationalIdHash`, `nationalIdMasked`, `details`.
- National ID is hashed deterministically with HMAC-SHA256 using a server-side pepper, and masked as `******last4`.

## Identification Decision Rules

- `score ≥ matched_threshold` (0.6) → `matched`
- `possible_match_threshold ≤ score < matched_threshold` (0.4 ≤ score < 0.6) → `possible_match`
- `score < possible_match_threshold` → `no_match`

## Qdrant Collection Naming

`face_samples_<modelName>_<embeddingDimension>_<modelVersion>`

Example: `face_samples_arcface_w600k_r50_batch_512_batch`

Distance metric: cosine.

## Testing Strategy

- All tests run on a machine without CUDA.
- `torch`, `torchvision`, `tensorrt`, `cupy` are lazy-imported in production code.
- Unit tests mock the TensorRT session and torch tensors, using CPU numpy equivalents where needed.
- Integration tests use FastAPI `TestClient` with repository/adapter mocks.

## Verification

- `pytest backend/tests -q`
- `ruff check backend/app backend/tests`
- `ruff format --check backend/app backend/tests`
- `mypy backend/app`
- Grep checks for forbidden routes and GPU UUID hardcoding.
