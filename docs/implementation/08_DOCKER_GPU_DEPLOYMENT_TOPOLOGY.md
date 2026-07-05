# 08 Docker GPU Deployment Topology

> **Reference-first sources:** `docs/architecture/RUNTIME_TOPOLOGY.md`, `docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`, Context7 (Docker Compose, Nginx), deepwiki `docker/compose`, deepwiki `nginx/nginx`.

## Goal

Document the dev and GPU-demo deployment topologies. The same backend image must run in all modes; GPU pinning happens only in Docker Compose or orchestrator configuration, never in Python.

## Runtime topology summary

### Dev / simple mode

```text
client
  → api:8000
    → postgres:5432
    → qdrant:6333
    → minio:9000
```

- Single `api` service, CPU or whatever GPU is available via env.
- No nginx load balancer.
- Uses host-mounted model artifacts.

### GPU demo mode

```text
client
  → api-lb / nginx :80
    → api-gpu-0 :8000  → GPU 0 (Docker pinned)
    → api-gpu-1 :8000  → GPU 1 (Docker pinned)
    → api-gpu-2 :8000  → GPU 2 (Docker pinned)
       ↓
    postgres, qdrant, minio (shared)
```

- All `api-gpu-*` services run the same backend image and same code.
- Each container sees its pinned GPU as `cuda:0`.
- Python ONNX Runtime uses `device_id=0` and `CUDAExecutionProvider`.
- PostgreSQL, Qdrant, MinIO are shared stateful services.
- Replicas are stateless; a request can hit any backend.

## How others implement this

### Docker Compose GPU reservations

DeepWiki analysis of `docker/compose` shows GPU allocation is configured via `deploy.resources.reservations.devices`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
          device_ids: ['0']
```

To pin replicas to distinct GPUs, separate service definitions are used, each with a different `device_ids` entry.

### Nginx upstream load balancing

The `nginx/nginx` patterns use an `upstream` block and `proxy_pass`:

```nginx
upstream fastapi_backends {
    server api-gpu-0:8000;
    server api-gpu-1:8000;
    server api-gpu-2:8000;
    keepalive 64;
}

server {
    listen 80;
    location / {
        proxy_pass http://fastapi_backends;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Nginx supports round-robin, least-connections, and IP-hash load-balancing algorithms. Passive health checks use `max_fails` and `fail_timeout`.

## How MergenVision will adapt this

- **Single backend Dockerfile**:
  - Based on a Python image with CUDA runtime for GPU demo; CPU-only base image is acceptable for dev mode if env disables CUDA.
  - Installs Python deps.
  - Copies `backend/app` and `artifacts/model_benchmarks/MODEL_MANIFEST.json`.
  - Does **not** hardcode GPU UUID or physical GPU index.
  - Exposes port `8000`.
- **GPU pinning in Compose**:
  - `api-gpu-0` → `device_ids: ['0']`.
  - `api-gpu-1` → `device_ids: ['1']`.
  - `api-gpu-2` → `device_ids: ['2']`.
  - Each container's `NVIDIA_VISIBLE_DEVICES` is set by the Compose device reservation. The container runtime maps the selected GPU to `/dev/nvidia0`, so ONNX sees it as `cuda:0`.
- **Environment variables**:
  - `ONNX_PROVIDER_PRIORITY=CUDAExecutionProvider,CPUExecutionProvider`
  - `ONNX_DEVICE_ID=0`
  - `QDRANT_HOST`, `QDRANT_PORT`, `POSTGRES_URL`, `MINIO_ENDPOINT`, `MINIO_BUCKET_*`
- **Nginx configuration**:
  - Reverse proxy with round-robin upstream.
  - Keepalive connections enabled.
  - Health endpoint `/health` used for passive checks (`max_fails=3 fail_timeout=30s`).
- **No production ten-million-shard topology** in Phase 1; the GPU-demo topology is for validation only.

## Files to be created in later phases

- `backend/Dockerfile`
- `backend/Dockerfile.cpu` (optional, for CPU-only builds)
- `docker-compose.yml` (dev)
- `docker-compose.gpu.yml` (GPU demo)
- `nginx/nginx.conf` or `nginx/default.conf`

## Verification plan

- `docker compose -f docker-compose.gpu.yml up` starts all services.
- `GET /health` returns 200 from nginx on each backend.
- `nvidia-smi` inside each `api-gpu-*` container confirms the expected GPU is visible as `cuda:0`.
- Batch identification request processed successfully on each GPU replica.
