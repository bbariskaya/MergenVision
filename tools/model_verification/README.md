# tools/model_verification

Phase 0B model verification scripts for MergenVision.

These scripts are read-only analysis/smoke tools. They do not modify model files,
backend code, or Docker configuration. They produce JSON artifacts under
`artifacts/model_benchmarks/results/`.

## Scripts

- `verify_model_manifest.py`  
  Compares downloaded model files against the SHA-256/size entries in
  `artifacts/model_benchmarks/MODEL_MANIFEST.json` (read-only) and writes
  `artifacts/model_benchmarks/results/phase0b_manifest_verification.json`.

- `inspect_onnx_shapes.py`  
  Loads each primary ONNX model with `onnx` and records input/output tensor
  names, shapes, and dtypes. Writes
  `artifacts/model_benchmarks/results/phase0b_onnx_shapes.json`.

- `ort_provider_smoke.py`  
  Probes available ONNX Runtime execution providers and attempts to load each
  primary model with `CPUExecutionProvider`, `CUDAExecutionProvider`, and
  `TensorrtExecutionProvider` (with CPU fallback). Writes
  `artifacts/model_benchmarks/results/phase0b_ort_providers.json`.

- `dummy_batch_smoke.py`  
  Runs dummy NumPy inputs through the primary detector/recognizer for
  batch sizes `1 4 8 16 32` on a selected execution provider. Verifies that
  batch-scaled output shapes are produced. Writes
  `artifacts/model_benchmarks/results/phase0b_dummy_batch_<provider>.json`.

## Running

```bash
/home/user/.venv/bin/python tools/model_verification/verify_model_manifest.py
/home/user/.venv/bin/python tools/model_verification/inspect_onnx_shapes.py
/home/user/.venv/bin/python tools/model_verification/ort_provider_smoke.py
/home/user/.venv/bin/python tools/model_verification/dummy_batch_smoke.py --provider CPUExecutionProvider --batch-sizes 1 4 8 16 32
/home/user/.venv/bin/python tools/model_verification/dummy_batch_smoke.py --provider CUDAExecutionProvider --batch-sizes 1 4 8 16 32
```

The `CUDAExecutionProvider` run is skipped automatically if CUDA is unavailable.
