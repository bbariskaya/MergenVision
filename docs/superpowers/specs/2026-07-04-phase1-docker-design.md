# Phase 1 Docker & Runtime Design Specification

## Goal
Package the MergenVision Phase 1 backend and frontend into container images and provide two Docker Compose environments: a single-API dev/simple mode and a multi-GPU demo mode.

## Constraints
- One backend image serves both `api` and `api-gpu-*` services.
- GPU UUID/device pinning only in Docker Compose, never in Python.
- PostgreSQL, Qdrant, MinIO are shared across all modes.
- No Phase 2 services or separate data stacks.
- Frontend image is nginx serving static Vite build.
- Backend health/readiness endpoints must respond after `docker compose up --build`.

## Deployment Modes

### Mode A — Dev/Simple (`docker-compose.yml`)
- `frontend` (nginx:80) -> `api:8000` -> PostgreSQL, Qdrant, MinIO
- Use for local development without GPU scheduling.
- `api` may run on CPU or GPU depending on host; TensorRT engines mounted read-only.

### Mode B — GPU Demo (`docker-compose.gpu.yml`)
- `frontend` (nginx:80) -> `api-lb:8000` -> `api-gpu-0/1/2:8000` -> shared PostgreSQL, Qdrant, MinIO
- `api-lb` is nginx round-robin upstream.
- Each `api-gpu-N` pinned to one physical GPU via `CUDA_VISIBLE_DEVICES` and `deploy.resources.reservations.devices`.
- Inside container each replica sees its assigned GPU as `cuda:0`.

## Backend Image
- Base: `nvidia/cuda:12.0.1-runtime-ubuntu22.04`
- Python 3.12, `uv` installer, synchronized `uv.lock`.
- Source copied to `/app/app`, `/app/scripts`, `/app/tests`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Health check: `curl -f http://localhost:8000/health`.
- TensorRT engines mounted read-only at `/app/artifacts/trt_engines`.
- Runs as non-root `appuser`.

## Frontend Image
- Build stage: `node:20-alpine` runs `npm ci && npm run build`.
- Runtime stage: `nginx:alpine` serves `/usr/share/nginx/html`.
- SPA fallback: `try_files $uri $uri/ /index.html`.
- `/api/` proxied to `${API_BASE_URL}`.

## Network / Configuration
- Services communicate via Docker DNS names: `postgres`, `qdrant`, `minio`, `api`, `api-lb`, `api-gpu-*`.
- Backend config reads env vars:
  - `DATABASE_URL`
  - `QDRANT_URL`
  - `MINIO_URL` (or `MINIO_ENDPOINT` alias)
  - `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`
  - `TRT_ENGINE_DIR`
  - `GPU_DEVICE_ID`
  - `NATIONAL_ID_PEPPER`
- Frontend runtime proxy `API_BASE_URL` from Compose env.

## Persistent Volumes
- `pgdata`: PostgreSQL data.
- `qdrant_storage`: Qdrant collections.
- `minio_data`: object storage.

## Verification
- `docker compose up --build -d`
- `curl http://localhost:8000/health` -> `{"status":"ok"}`
- `curl http://localhost:8000/ready` -> `{"status":"ready",...}`
- GPU mode verifies same endpoints through `api-lb:8000`.
