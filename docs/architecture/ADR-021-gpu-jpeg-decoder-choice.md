# ADR-021: GPU JPEG Decode Strategy — DALI vs PIL Fallback

## Status

Proposed — awaiting approval.

## Context

`docs/fastestplan.md` targets ~1 minute for LFW (~13K images) with ≥220 img/s throughput. Its flowchart assumes "nvJPEG decode" so the entire pipeline (decode → resize → detector → NMS → align → recognizer → normalize) stays on GPU. Only the final `[N,512]` embeddings move to CPU.

Current Phase 1 implementation uses `GpuPilDecoder`, which decodes JPEG/PNG bytes with Pillow on CPU and then moves tensors to CUDA. The CPU decode + H2D copy becomes the bottleneck for batch throughput and likely prevents hitting the 1-minute LFW target.

## Options

### Option A — Keep `GpuPilDecoder` as primary decoder
- **Pros**: No new runtime dependency; works in CPU-only environments and mock-based tests; simpler code; aligns with current design spec.
- **Cons**: CPU decode limits throughput; `fastestplan.md` targets become unrealistic.
- **Mitigation**: Update `fastestplan.md` to reflect actual throughput with CPU decode (likely much lower than 220 img/s).

### Option B — Add `nvidia-dali` GPU decoder with optional PIL fallback
- **Pros**: Real `device="mixed"` GPU JPEG decode via nvJPEG; keeps the whole GPU pipeline on CUDA and can approach fastest-plan targets.
- **Cons**:
  - New runtime dependency on `nvidia-dali` and CUDA driver 525.60+ / Linux x64.
  - DALI cannot run on CPU-only hosts; tests must mock it or fall back to PIL.
  - Larger Docker image and deployment complexity.
  - Requires a refactor of `FacePipeline` and a new `GpuDaliDecoder` adapter boundary.
- **Implementation sketch**:
  1. Add `nvidia-dali` (CUDA 12 variant) to `pyproject.toml` as optional/lazy dependency.
  2. Create `app/infrastructure/adapters/gpu_dali_decoder.py` implementing a batched JPEG→CUDA tensor decoder using `fn.external_source` + `fn.decoders.image(device="mixed")` + `fn.resize` + `fn.crop_mirror_normalize`.
  3. Modify `FacePipeline` to choose DALI decoder when a CUDA device is available and DALI imports successfully; otherwise fall back to `GpuPilDecoder`.
  4. Add unit tests that mock `nvidia.dali` and integration tests that exercise the fallback path.
  5. Keep `GpuPilDecoder` as the CPU-test/development fallback.

### Option C — Revert to `cupyx` nvJPEG (from fastestplan.md diagram)
- CuPy's `cupyx` nvJPEG wrapper is less stable and less documented than DALI and was explicitly rejected earlier because stable Python bindings were not available. **Not recommended.**

## Recommendation

Adopt **Option B** with a strict fallback rule: DALI is used only when CUDA is available and the import succeeds; otherwise `GpuPilDecoder` runs. This keeps `fastestplan.md` targets achievable in GPU environments while preserving testability and CPU-development workflows.

## Consequences

- `pyproject.toml` gains `nvidia-dali-cuda120` (or equivalent) as a dependency.
- A new `GpuDaliDecoder` adapter is added to the model boundary list alongside `GpuPilDecoder`.
- `FacePipeline` gains runtime decoder selection logic controlled by config (`decoder_backend: dali | pil`).
- Tests must isolate DALI via mocks; repository CI likely stays CPU-only and exercises only the PIL path.
- `docs/superpowers/specs/2026-07-04-phase1-tensorrt-gpu-rewrite-design.md` and `docs/superpowers/plans/2026-07-04-phase1-tensorrt-gpu-rewrite-plan.md` must be updated.
- If rejected, `docs/fastestplan.md` must be revised to slower, CPU-decode-based targets.

## Decision

Awaiting project owner approval.
