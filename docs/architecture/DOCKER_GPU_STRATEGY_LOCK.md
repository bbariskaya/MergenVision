# Docker / GPU Strategy Lock

> **Status:** Accepted  
> **Scope:** Development, demo, and production-later deployments.

This document locks how Docker and GPU resources may be used in MergenVision. No code or Compose file may contradict it.

## Deployment Modes

### Mode A — Development / Simple

```text
frontend or API client
    -> api
    -> PostgreSQL / Qdrant / MinIO
```

Use this mode for:

- Local development without a GPU.
- CPU-only ONNX Runtime testing.
- Integration tests without GPU scheduling complexity.

Rules:

- One `api` container.
- The same backend image is used in all modes.
- The `api` container may run on CPU or GPU depending on environment.
- PostgreSQL, Qdrant, and MinIO may run as local services or containers.

### Mode B — GPU Demo

```text
frontend or API client
    -> api-lb / nginx
    -> api-gpu-0
    -> api-gpu-1
    -> api-gpu-2
    -> shared PostgreSQL
    -> shared Qdrant
    -> shared MinIO
```

Use this mode for:

- Multi-GPU demonstrations.
- Load distribution across physical GPUs without changing code.

Rules:

- `api-gpu-0`, `api-gpu-1`, `api-gpu-2` run the **same backend image**.
- `api-gpu-0`, `api-gpu-1`, `api-gpu-2` run the **same backend code**.
- Each `api-gpu-N` container is pinned to exactly one physical GPU.
- Each container typically sees that physical GPU as `cuda:0`.
- GPU UUID / device pinning is allowed **only** in Docker Compose or orchestrator configuration.
- Python application code must **not** hardcode GPU UUID.
- Python application code must **not** assume a physical GPU index.
- `api-lb` / nginx distributes requests without GPU-aware logic.
- PostgreSQL, Qdrant, and MinIO are shared by all API replicas.
- API replicas must be stateless.

### Mode C — Production (Later)

- Move GPU scheduling out of Docker Compose into an orchestrator (e.g., Kubernetes NVIDIA device plugin).
- Keep the same backend image and same code.
- Keep one shared PostgreSQL, one shared Qdrant, one shared MinIO.
- GPU pinning via orchestrator/device plugin, not application logic.

## GPU Pinning Rules

Allowed only in deployment configuration:

- Docker Compose `deploy.resources.reservations.devices` with `device_ids` or `count`.
- Kubernetes NVIDIA device plugin / node selector.
- Equivalent orchestrator-level mechanisms.

Forbidden in application code:

- Hardcoded GPU UUID strings.
- `torch.cuda.set_device(N)` based on a fixed assumption.
- `CUDA_VISIBLE_DEVICES` set inside Python code.
- Any code that maps a worker index to a physical GPU index.

## Shared Data Platform

- One logical PostgreSQL cluster.
- One logical Qdrant cluster.
- One logical MinIO cluster.
- Phase 1 and Phase 2 share the same services.
- Separation is by **table**, **collection name**, and **object prefix**, not by separate stacks.
- No permanent separate Phase 1/Phase 2 PostgreSQL/Qdrant/MinIO stacks.
- Temporary lab stacks are allowed only for development/testing and must not be treated as final architecture.

## Backend Image Rule

- All API containers (`api`, `api-gpu-*`, future video API) use the same backend image.
- The image contains all adapter code but starts only the services configured by environment variables.
- No separate "GPU-only" image.
- No separate "video-only" image for Phase 2; `worker-gpu` services use the same image with a different entrypoint/command.

## Phase 2 Worker-GPU Services

When Phase 2 is implemented:

- Video processing runs in separate `worker-gpu` services.
- The API submits jobs to a queue and reads results.
- Workers process video.
- Workers use the same detector/recognizer adapter code as the API.
- Workers search the same Qdrant identity collections as the API.
- Workers read/write the same MinIO bucket/prefix conventions as the API.

## Configuration Principles

- GPU enablement is configured via environment variables (e.g., `GPU_ENABLED=true`).
- The provider list is constructed from configuration, not from hardcoded strings.
- ONNX Runtime provider priority: `CUDAExecutionProvider` if available and configured, otherwise `CPUExecutionProvider`.
- GPU UUIDs, device counts, and worker replica counts belong in runtime configuration, never in source code.

## Forbidden Patterns

- Different backend images for `api-gpu-*` replicas.
- Python code that assumes `cuda:0` is always one specific physical GPU.
- Hardcoded `NVIDIA_VISIBLE_DEVICES` or `CUDA_VISIBLE_DEVICES` inside Python.
- Separate permanent Phase 1 and Phase 2 data stacks.
- GPU-aware routing logic inside the application.

## Reference Docs

- `docs/architecture/RUNTIME_TOPOLOGY.md` — topology diagrams.
- `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md` — data platform rationale.
- `docs/architecture/ARCHITECTURE_DECISION_RECORDS.md` — ADR-007 and related ADRs.
