REFERENCE_CHECK

Task:
Rewrite the Phase 1 MergenVision backend with a full-GPU TensorRT/torch/torchvision/cupy inference stack, add the `face_identity` table, and implement the complete set of Phase 1 REST endpoints and tests.

Phase:
Phase 1 (photo-based person recognition). Phase 2/3 design influence only via the stable `faceId` and shared services.

Allowed scope:
- All Phase 1 runtime routes: /health, /ready, /people, /people/{personId}/photos, /identify, /identification-requests, /audit, /stats, /media/{bucket}/{objectKey}.
- All Phase 1 tables: person, person_photo, face_identity, face_sample, identification_request, identification_query_face, identification_result, audit_log.
- TensorRT adapters and offline engine build script; real engine build deferred to a matching CUDA/cuDNN/TensorRT environment.
- Alembic migration for the Phase 1 schema.
- Unit/API tests with mocked GPU stack.

Files allowed to change:
- backend/pyproject.toml
- backend/alembic.ini and backend/alembic/*
- backend/app/core/*
- backend/app/domain/models.py
- backend/app/schemas/*
- backend/app/infrastructure/*
- backend/app/repositories/*
- backend/app/application/*
- backend/app/api/*
- backend/app/main.py
- backend/tests/*
- backend/scripts/*
- docs/superpowers/specs/* and docs/superpowers/plans/*
- docs/architecture/* governance docs
- AGENTS.md, CLAUDE.md

Files forbidden to change:
- Placeholder / future routes (no /videos/*, /imports/*, /faces/*, /oracle/*, /objects/*, /streams/*).
- model/dataset download scripts beyond the committed build scripts.
- Any Docker Compose or production Dockerfile (out of scope for this task).
- requirements/ source files (read-only).

Local docs checked:
- requirements/phase1recognitionrequirements.md
- requirements/phase2videorequirements.md
- opensourceReferences/references.md
- docs/superpowers/specs/2026-07-04-phase1-tensorrt-gpu-rewrite-design.md
- docs/superpowers/plans/2026-07-04-phase1-tensorrt-gpu-rewrite-plan.md
- docs/architecture/API_CONTRACT.md
- docs/architecture/DATA_MODEL.md
- docs/architecture/ARCHITECTURE_DECISION_RECORDS.md
- docs/architecture/DIAGRAM_INDEX.md
- docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md
- docs/architecture/MODEL_ADAPTER_BOUNDARY.md
- artifacts/model_benchmarks/MODEL_MANIFEST.json

Architecture docs checked:
- API_CONTRACT.md (Phase 1 endpoints and responses)
- DATA_MODEL.md (tables, columns, Qdrant payload, collection naming)
- ARCHITECTURE_DECISION_RECORDS.md (ADR-006, ADR-007, ADR-010, ADR-011, ADR-012, ADR-017, ADR-019, ADR-020, ADR-021, ADR-022)
- DOCKER_GPU_STRATEGY_LOCK.md
- MODEL_ADAPTER_BOUNDARY.md

Requirements checked:
- Phase 1 requirements (REQ-001..REQ-007): Oracle and 10M scale are future/out of Phase 1 scope.
- Phase 2 requirements: informs `face_identity` table and stable faceId, but Phase 2 routes/tables are forbidden.

Official docs checked via context7:
- FastAPI request files / dependencies / testclient (to be queried if router test issues arise)
- SQLAlchemy 2.0 async ORM / quickstart / session basics
- Alembic tutorial
- Qdrant collections / points / search / filtering
- MinIO Python API
- TensorRT Python API (to be queried during adapter implementation)
- Docker Compose GPU runtime (not needed for implementation; already locked)

Open-source references checked via exa/web:
- InsightFace SCRFD detection decoding from github.com/deepinsight/insightface (used via the existing numpy implementation in old detector_adapter.py)
- InsightFace ArcFace preprocessing and 5-landmark alignment template (arcface_dst)
- Hugging Face model repository: alonsorobots/scrfd_320_batched (model source, shapes)

Existing local code inspected:
- Restored backend skeleton: pyproject.toml, app/core/config.py, errors.py, ids.py, logging.py, app/main.py, api/v1/router.py, infrastructure/db.py, adapters/detector_adapter.py, adapters/recognizer_adapter.py (ONNX versions)
- Old tests for detector, recognizer, and ort_session

Old lessons checked:
- olderDiagramsProvedWrog/ (noted; avoided old architecture errors)
- /home/user/Demo/Demo12_VGGFace2Lab/docs/ and /home/user/Demo/VideoFaceGpuLab/docs/ (cautionary context; not directly reused)

Patterns to follow:
- FastAPI + async SQLAlchemy 2.0 + Alembic + Pydantic v2
- Clean adapter boundary: ImageValidator, DetectorAdapter, AlignerPreprocessor, RecognizerAdapter, FacePipeline
- Repository pattern over SQLAlchemy
- UUIDv7 for IDs
- Data ownership split: PostgreSQL metadata, Qdrant vectors, MinIO bytes
- Lazy import of GPU packages so tests run without CUDA
- TDD: failing test first, then implementation
- Offline TensorRT engine build for static batch sizes [1,8,16,32]
- CPU boundary at final [N,512] embedding

Patterns rejected:
- ONNX Runtime CUDAExecutionProvider on the hot path (removed, per ADR-019)
- Runtime-built TensorRT engines (cold-start penalty; use offline build)
- Direct numpy/OpenCV-based hot path for detector/aligner/recognizer (rewritten in torch)
- Per-person-only identity (replaced by `face_identity` stable face-level ID)
- Storing sensitive data or embeddings in Qdrant/audit

Architecture decisions that apply:
- ADR-001 root-level API
- ADR-002 shared data platform
- ADR-003 PostgreSQL as metadata source of truth
- ADR-004 Qdrant as vector index only
- ADR-005 MinIO as object storage
- ADR-006 adapter boundary
- ADR-007 one API replica per physical GPU
- ADR-010 UUIDv7
- ADR-011 model/dimension/version-specific Qdrant collections
- ADR-012 no fake runtime pipeline (tests use mocks, production code routes to real engines)
- ADR-017 Phase 1 scope lock
- ADR-019 TensorRT/torch GPU-only stack
- ADR-020 stable `face_identity` table
- ADR-021 offline static-batch engines
- ADR-022 CPU boundary at final embedding

Docker/GPU strategy that applies:
- Dev/simple mode: single api container -> PostgreSQL/Qdrant/MinIO.
- GPU demo mode: nginx -> api-gpu-* containers, each pinned one physical GPU, seeing cuda:0.
- Python code uses `gpu_device_id` from config only; no UUID hardcoding.

Data ownership rules that apply:
- PostgreSQL: person, face_identity, person_photo, face_sample metadata, identification_request/history/results, audit_log.
- Qdrant: embeddings + reference-only payload.
- MinIO: original images, face crops, query images if retained.

Security/PII rules that apply:
- National ID hashed and masked; never expose raw national ID.
- Never store raw national ID, image bytes, embeddings, or full sensitive person details in Qdrant or audit.
- Never store raw embedding vectors or image bytes in PostgreSQL.

Tests/verification planned:
- Unit tests: people service, photo/enrollment service, identification service, stats service, ids, config, repositories, storage, vector store, image validator.
- Adapter tests with mocked TensorRT/torch.
- API tests for every Phase 1 endpoint with mocked services.
- Full suite: pytest backend/tests -q
- Lint: ruff check backend; ruff format --check backend
- Typecheck: mypy backend/app
- Grep checks for forbidden routes and GPU UUID hardcoding

Unverified assumptions:
- SCRFD batched ONNX outputs follow the `[B, total_anchors, C]` order used by the prior numpy decoder; the TensorRT engine preserves this order.
- ArcFace batched ONNX outputs `[N,512]` unnormalized (L2 normalization performed in adapter).
- A matching CUDA/cuDNN/TensorRT environment will exist for real engine build and benchmark; current local env is missing cuDNN 9.
- qdrant-client async client and MinIO client signatures used are current stable versions.

Approval gates:
- User explicitly said "sil backendi yeniden yaz" and "başla".
- Plan and spec already cover face_identity and TensorRT stack.

Out-of-scope requests detected:
- Phase 2/3 routes and tables.
- Docker Compose / nginx / production deployment.
- Real LFW benchmark until a GPU/TensorRT environment is available.
