# Phase 1 Dockerize Implementation Plan

## Goal
Build container images and Docker Compose files for MergenVision Phase 1 backend and frontend, then verify health/readiness endpoints come up successfully.

## Global Constraints
- Single backend image for `api` and all `api-gpu-*` replicas.
- GPU pinning only in Docker Compose.
- No Phase 2 services.
- No changes to business logic/API surface.
- `docker compose up --build` must pass verification before marking done.

---

### Task 1: Backend Dockerfile
**Files:**
- Create: `backend/Dockerfile`

**Steps:**
1. Use base `nvidia/cuda:12.0.1-runtime-ubuntu22.04`.
2. Install Python 3.12, curl, ca-certificates, and pip-provided `uv`.
3. Set workdir `/app`.
4. Copy `pyproject.toml`, `uv.lock`, `app/`, `scripts/`, `tests/`.
5. Run `uv sync --frozen --no-dev`.
6. Create `appuser`, chown `/app`, switch user.
7. Expose 8000, add HEALTHCHECK, CMD uvicorn.

**Verification:** `docker build -f backend/Dockerfile backend/ --tag mergenvision-backend:test` succeeds.

---

### Task 2: Frontend Init and Dockerfile
**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Modify: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.*`
- Create/delete: adjust Tailwind from v4 to v3 per user commands.

**Steps:**
1. Ensure Vite React TS project exists.
2. Install `tailwindcss postcss autoprefixer` and init `tailwind.config.js` / `postcss.config.js`.
3. Configure Tailwind content paths and import directive in CSS.
4. Install `react-router-dom @tanstack/react-query axios zustand react-hook-form lucide-react`.
5. Write `Dockerfile`: build with `node:20-alpine`, runtime `nginx:alpine`.
6. Write `nginx.conf` with SPA fallback and `/api/` proxy to `${API_BASE_URL}`.

**Verification:** `docker build -f frontend/Dockerfile frontend/ --tag mergenvision-frontend:test --build-arg API_BASE_URL=http://api:8000` succeeds.

---

### Task 3: Docker Compose Dev/Simple
**Files:**
- Create: `docker-compose.yml`

**Steps:**
1. Define services: `postgres`, `qdrant`, `minio`, `api`, `frontend`.
2. Configure shared volumes.
3. Set backend env for Docker network hosts.
4. Mount `artifacts/trt_engines` read-only into `api`.
5. Expose ports: `8000:8000`, `80:80`, `5432:5432`, `6333:6333`, `9000:9000`, `9001:9001`.

**Verification:** `docker compose up --build -d` starts all services.

---

### Task 4: Docker Compose GPU Demo
**Files:**
- Create: `docker-compose.gpu.yml`
- Create: `docker/nginx.conf`

**Steps:**
1. Define `api-lb` nginx load balancer.
2. Define `api-gpu-0`, `api-gpu-1`, `api-gpu-2` from same backend image.
3. Set `CUDA_VISIBLE_DEVICES` 0/1/2 per replica.
4. Add `deploy.resources.reservations.devices` nvidia GPU reservation.
5. Define shared `postgres`, `qdrant`, `minio`.
6. Configure `frontend` to point to `api-lb:8000`.

**Verification:** `docker compose -f docker-compose.gpu.yml up --build -d` starts LB and GPU replicas if NVIDIA runtime available.

---

### Task 5: Config, Ignore, and Env Files
**Files:**
- Create: `backend/.dockerignore`
- Create: `frontend/.dockerignore`
- Create: `backend/.env.example`
- Create: `frontend/.env.example`
- Modify: `backend/app/core/config.py`

**Steps:**
1. Add `.dockerignore` entries for venv, cache, git, env, markdown.
2. Add `.env.example` files with sensible local and Docker defaults.
3. Update `config.py` to support `MINIO_ENDPOINT` alias and confirm all Docker host env vars map correctly.

**Verification:** `python -c "from app.core.config import Settings; print(Settings())"` resolves from `.env.example` without errors (if run locally with unset defaults).

---

### Task 6: Runtime Verification
**Files:** None

**Steps:**
1. `docker compose up --build -d`
2. Wait for `api` health.
3. `curl http://localhost:8000/health`
4. `curl http://localhost:8000/ready`
5. Inspect logs: `docker compose logs -f api`
6. Tear down: `docker compose down`
7. If GPU runtime available, repeat with `docker-compose.gpu.yml`.

**Verification:** Both `health` and `ready` return expected JSON and HTTP 200/503 semantics; logs show no startup crash.
