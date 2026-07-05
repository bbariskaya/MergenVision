# Phase 1A Implementation Planning Index

> **Scope lock:** This directory contains planning documents only. No backend code, frontend code, migrations, Docker Compose/production Dockerfile, API routes, runtime services, model adapters, Qdrant collections, or inference scripts are created in Phase 1A.

## Goal

Provide a complete, reference-first implementation plan for building the MergenVision Phase 1 photo-based person-recognition platform, scoped strictly to the allowed Phase 1 runtime routes and tables defined in the architecture documents.

## Package contents

| # | Document | Focus |
|---|----------|-------|
| 01 | `01_BACKEND_FASTAPI_PROJECT_STRUCTURE.md` | Backend layout, layers, request flow |
| 02 | `02_SQLALCHEMY_ALEMBIC_DATA_ACCESS.md` | PostgreSQL ORM, repository pattern, migrations |
| 03 | `03_QDRANT_VECTOR_LAYER.md` | Vector collection strategy, upsert/search |
| 04 | `04_MINIO_MEDIA_STORAGE_LAYER.md` | Object storage, presigned URLs, retention |
| 05 | `05_MODEL_ADAPTER_AND_INFERENCE_INTEGRATION.md` | ONNX Runtime adapters and pipelines |
| 06 | `06_SERVICE_LAYER_AND_DOMAIN_MODEL.md` | Domain model and service-layer responsibilities |
| 07 | `07_REST_API_CONTRACT_IMPLEMENTATION_PLAN.md` | Allowed routes mapped to implementation files |
| 08 | `08_DOCKER_GPU_DEPLOYMENT_TOPOLOGY.md` | Dev and GPU-demo topologies |
| 09 | `09_TESTING_AND_QUALITY_STRATEGY.md` | Test pyramid, fixtures, verification gates |
| 10 | `10_SECURITY_AND_PII_HANDLING.md` | PII rules, audit, input validation |
| 11 | `11_PHASE_1A_SCOPE_LOCK_AND_PHASE_2_HANDOFF.md` | Forbidden Phase 1 work and Phase 2 handoff criteria |

## Sources of truth

All planning documents assume the reader has already read:

- `docs/architecture/API_CONTRACT.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/RUNTIME_TOPOLOGY.md`
- `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`
- `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`
- `docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md`
- `docs/architecture/SENSITIVE_DATA_RULES.md`
- `docs/architecture/FUTURE_BOUNDARIES.md`
- `docs/architecture/ARCHITECTURE_DECISION_RECORDS.md`
- `docs/model_research/PHASE_0B_MODEL_SHAPE_PROVIDER_BATCH_REPORT.md`
- `docs/model_research/PHASE_0B_GPU_DOCKER_VERIFICATION_REPORT.md`
- `artifacts/model_benchmarks/MODEL_MANIFEST.json`

## Notes on repository state

- `backend/` and `frontend/` exist as pre-existing empty untracked directories.
- They are **not** treated as scaffold completion and receive no files in Phase 1A.
- All implementation file paths inside the planning documents are targets for later phases.
