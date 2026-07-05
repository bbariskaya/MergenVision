# Dockerize Reference Check — Phase 1 Runtime

```text
REFERENCE_CHECK

Task: MergenVision Phase 1 backend/frontend Dockerize ve Docker Compose GPU demo modu
Phase: Phase 1
Allowed scope:
  - backend/Dockerfile
  - frontend/Dockerfile (mevcut Vite init üzerinden)
  - frontend/nginx.conf
  - docker-compose.yml (dev/simple)
  - docker-compose.gpu.yml (GPU demo)
  - docker/nginx.conf (GPU load balancer)
  - backend/.dockerignore, frontend/.dockerignore
  - backend/.env.example, frontend/.env.example
  - backend/app/core/config.py (Docker host/env desteği)
Files allowed to change:
  - backend/Dockerfile
  - frontend/Dockerfile
  - frontend/nginx.conf
  - docker-compose.yml
  - docker-compose.gpu.yml
  - docker/nginx.conf
  - backend/.dockerignore
  - frontend/.dockerignore
  - backend/.env.example
  - frontend/.env.example
  - backend/app/core/config.py
  - docs/superpowers/specs/*-docker-design.md
  - docs/superpowers/plans/*-docker-plan.md
Files forbidden to change:
  - backend application logic (endpoint'ler, servisler, model adaptörleri)
  - frontend UI/UX sayfaları (henüz yapılmayacak)
  - migrations
  - API_CONTRACT.md, DATA_MODEL.md harici dokümanlar
Local docs checked:
  - docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md
  - docs/architecture/API_CONTRACT.md
  - docs/architecture/RUNTIME_TOPOLOGY.md (参考资料)
  - AGENTS.md
  - CLAUDE.md
Architecture docs checked: evet
Requirements checked: evet
Official docs checked via context7:
  - Docker Compose deploy.resources.reservations.devices GPU syntax
  - Nginx upstream/proxy_pass basics (redirect sonrası)
Open-source references checked via exa/web: kullanıcı tarafından sağlanan exact Dockerfile/Compose snippet'leri primary referans.
Existing local code inspected:
  - backend/app/core/config.py
  - backend/app/main.py
  - backend/app/infrastructure/db.py
  - backend/app/infrastructure/health_checks.py
  - backend/pyproject.toml
  - backend/uv.lock
  - frontend/package.json
  - frontend/vite.config.ts (mevcut init)
Old lessons checked: N/A
Patterns to follow:
  - backend image tek; api-gpu-* aynı image'ı kullanır.
  - GPU pinning sadece Compose/orkestratör config'inde.
  - Python kodda GPU UUID/index hardcode yok.
  - PostgreSQL/Qdrant/MinIO shared; Phase 1/Phase 2 ayrı stack yok.
  - Ready probe dependency check: PostgreSQL SELECT 1, Qdrant get_collections, MinIO list_buckets.
  - Health sadece liveness döner.
Patterns rejected:
  - Phase 2 worker servisleri eklemek.
  - Ayrı "GPU-only" image.
  - Python içinde CUDA_VISIBLE_DEVICES set etmek.
  - Uydurma endpoint/veritabanı tablosu.
Architecture decisions that apply:
  - Mode A: dev/simple (client -> api -> PG/Qdrant/MinIO)
  - Mode B: GPU demo (client -> api-lb/nginx -> api-gpu-0/1/2 -> shared PG/Qdrant/MinIO)
  - Backend image aynı; service farkı yalnız env/CUDA_VISIBLE_DEVICES.
Docker/GPU strategy that applies:
  - nvidia/cuda:12.0.1-runtime-ubuntu22.04 bazlı backend image.
  - node:20-alpine build + nginx:alpine frontend image.
  - GPU demo'da deploy.resources.reservations.devices nvidia driver count 1 capabilities [gpu].
  - Her api-gpu-* farklı CUDA_VISIBLE_DEVICES (0/1/2) ve container içinde kendi cuda:0 görür.
Data ownership rules that apply:
  - PostgreSQL: person/photo/metadata/request/audit
  - Qdrant: embedding'ler (paylaşılan)
  - MinIO: image bytes (paylaşılan bucket'lar)
Security/PII rules that apply:
  - .env.example'da gerçek secret yerine placeholder.
  - national_id_pepper için placeholder belirtilmiş.
Tests/verification planned:
  - docker compose up --build -d
  - curl http://localhost:8000/health
  - curl http://localhost:8000/ready
  - docker compose -f docker-compose.gpu.yml up --build -d (opsiyonel, host'ta NVIDIA runtime varsa)
  - docker compose logs ile log doğrulama
Unverified assumptions:
  - Host'ta Docker + docker compose kurulu.
  - GPU mod için NVIDIA Container Toolkit kurulu.
  - artifacts/trt_engines/*.plan dosyaları mevcut (önceki TensorRT build'inde üretildi).
  - Backend container başlangıcında tablo oluşturulması için ayrı migration/init adımı gerekebilir; şimdilik readiness probe SELECT 1 ile sınırlı.
Approval gates:
  - Kullanıcı exact Dockerfile/Compose içeriği sağladı; onaylanmış kabul ediliyor.
Out-of-scope requests detected:
  - Phase 2 worker-gpu servisleri şimdilik eklenmiyor.
  - UI sayfaları şimdilik yapılmıyor.
```
