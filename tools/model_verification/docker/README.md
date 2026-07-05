# Docker verification image for Phase 0B-GPU

This directory contains a one-off Docker image used **only** to verify that
ONNX Runtime `CUDAExecutionProvider` can load and run the primary Phase 1
batch models (`scrfd_10g_320_batch.onnx` + `arcface_w600k_r50_batch.onnx`)
inside a controlled NVIDIA GPU container.

## Scope

- Verification-only. Not the production MergenVision API image.
- No backend, frontend, API server, database, or object storage.
- No model download inside the image (models are bind-mounted read-only from
  `artifacts/model_benchmarks/models/`).
- No host system CUDA/cuDNN changes.

## Files

- `Dockerfile.gpu-ort-smoke` — verification image definition.
- `README.md` — this file.

## Base image

`nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04`

Selected because `onnxruntime-gpu` 1.27.0 depends on
`nvidia-cuda-runtime-cu13 ~=13.0` and `nvidia-cudnn-cu13 ~=9.0`.

## Build

Use the orchestration script at `tools/model_verification/run_gpu_docker_verification.sh`.
Do not tag this image as `mergenvision-api` or any production image name.
