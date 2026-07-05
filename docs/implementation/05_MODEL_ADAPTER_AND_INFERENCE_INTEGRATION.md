# 05 Model Adapter and Inference Integration

> **Reference-first sources:** `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`, `docs/model_research/PHASE_0B_MODEL_SHAPE_PROVIDER_BATCH_REPORT.md`, `docs/model_research/PHASE_0B_GPU_DOCKER_VERIFICATION_REPORT.md`, `artifacts/model_benchmarks/MODEL_MANIFEST.json`, Context7 (ONNX Runtime), deepwiki `microsoft/onnxruntime`.

## Goal

Wrap SCRFD and ArcFace ONNX models in a clean adapter boundary so the business layer never sees raw model inputs/outputs, model paths, GPU indices, or preprocessing details.

## Verified Phase 0B model shapes

| Model | File | Input | Output | SHA256 |
|-------|------|-------|--------|--------|
| Detector | `scrfd_10g_320_batch.onnx` | `[N, 3, 320, 320]` | 9 batched multi-stride outputs | `875763ba0b0725de5097f2bf2900fb3690667f53ab0f642a0ad31f94581483f8` |
| Recognizer | `arcface_w600k_r50_batch.onnx` | `[N, 3, 112, 112]` | `[N, 512]` | `6afbf406aa229a439abbca7436cc42be254d4e3af6200d8b7ae4c1fec0c18f2f` |

- Batch sizes `1/4/8/16/32` passed CPU dummy inference.
- GPU `CUDAExecutionProvider` passed on GPU 1 and GPU 2 in Docker.
- GPU 0 was not tested because it was occupied by VLLM/EngineCore.

## How others implement this

Production ONNX Runtime patterns from `microsoft/onnxruntime`:

- Load an `InferenceSession` from a file path or bytes:

```python
import onnxruntime as ort
session = ort.InferenceSession("model.onnx")
```

- Select execution providers with fallback:

```python
session = ort.InferenceSession(
    "model.onnx",
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
)
```

- Provider options can pin a device id without hardcoding physical GPU UUID in Python:

```python
providers=[
    ("CUDAExecutionProvider", {"device_id": 0}),
    "CPUExecutionProvider",
]
```

- Run inference with a NumPy dict:

```python
outputs = session.run(None, {"input": input_array})
```

- Use `IOBinding` for zero-copy GPU inference when latency matters.
- Enable built-in fallback so an EP failure falls back to CPU.

## How MergenVision will adapt this

- **Model registry** (`app/infrastructure/model_registry.py`): loads `artifacts/model_benchmarks/MODEL_MANIFEST.json` and exposes detector/recognizer entries. Each entry contains `name`, `version`, `expectedInputShape`, `expectedOutputShape`, `sha256`, `embeddingDimension`, `preprocessor`, `mean`, `std`, `providerPriority`.
- **Adapter boundary** (`app/infrastructure/adapters/`):
  - `ImageValidator`: checks mime, size, dimensions, decodeability.
  - `DetectorAdapter`: accepts NumPy image, returns detected face bounding boxes and landmarks.
  - `AlignerPreprocessor`: crops and aligns face chips to recognizer input size using landmarks.
  - `RecognizerAdapter`: accepts aligned face chips, returns L2-normalized 512-D embeddings.
- **Pipeline classes** (pure orchestration):
  - `FacePipeline`: load both adapters, expose `detect(image)`, `recognize(face_chips)`.
  - `EnrollmentPipeline`: detect/align/recognize a person photo; produce `(sampleId, vector, payload)` for Qdrant plus metadata for PostgreSQL.
  - `OnlineIdentifyPipeline`: detect/align/recognize query image; run Qdrant search; return candidate scores.
- **Execution-provider selection**:
  - Default providers list from env: `CUDAExecutionProvider, CPUExecutionProvider`.
  - `device_id` comes from env `ONNX_DEVICE_ID` and defaults to `0`. Each `api-gpu-*` container is pinned to one physical GPU by Docker Compose and sees it as `cuda:0`; therefore Python uses `device_id=0` consistently.
  - If CUDA init fails, `InferenceSession` falls back to CPU automatically; services log the downgrade and continue.
- **Batching**:
  - Detector supports batch inference for Phase 1 photo processing.
  - Recognizer supports batch face-chip inference.
  - Max batch sizes are set via env/config and validated against model manifest.
- **No random or mock embeddings** in runtime code. Tests may use fixtures with synthetic deterministic vectors.
- **Model replacement rule**: changing recognizer may require creating a new Qdrant collection; existing samples must be re-enrolled. PostgreSQL `face_sample` rows carry `modelName`/`modelVersion` so the system can detect mismatches.

## Files to be created in later phases

- `backend/app/infrastructure/model_registry.py`
- `backend/app/infrastructure/adapters/image_validator.py`
- `backend/app/infrastructure/adapters/detector_adapter.py`
- `backend/app/infrastructure/adapters/aligner_preprocessor.py`
- `backend/app/infrastructure/adapters/recognizer_adapter.py`
- `backend/app/infrastructure/adapters/pipelines.py`

## Verification plan

- Unit-test each adapter with synthetic NumPy inputs matching verified shapes.
- Integration-test `FacePipeline` against the real `scrfd_10g_320_batch.onnx` and `arcface_w600k_r50_batch.onnx` on CPU.
- GPU smoke test in Docker pinned to one GPU (same image as production).
- Verify `MODEL_MANIFEST.json` SHA matches loaded model file; fail startup if mismatch.
