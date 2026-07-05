# 01 Backend FastAPI Project Structure

> **Reference-first sources:** `docs/architecture/API_CONTRACT.md`, `docs/architecture/RUNTIME_TOPOLOGY.md`, `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`, Context7 (FastAPI), deepwiki `fastapi/full-stack-fastapi-template`.

## Goal

Define a layered, single-image FastAPI backend layout that can serve both dev mode and GPU-demo mode with identical code, and that separates HTTP concerns, business logic, data access, and ML adapters.

## Target directory layout

```textnbackend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI factory, lifespan, router aggregation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings, env-driven
│   │   ├── logging.py          # structured logging setup
│   │   └── errors.py           # domain + HTTP exception hierarchy
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # FastAPI Depends factories (db, qdrant, minio, adapters)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # aggregates all v1 routers
│   │   │   ├── people.py
│   │   │   ├── photos.py
│   │   │   ├── identify.py
│   │   │   ├── identification_requests.py
│   │   │   ├── audit.py
│   │   │   ├── stats.py
│   │   │   └── media.py
│   ├── application/            # pure Python services / use cases
│   │   ├── __init__.py
│   │   ├── people_service.py
│   │   ├── photo_service.py
│   │   ├── identify_service.py
│   │   ├── audit_service.py
│   │   └── stats_service.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py           # domain entities and value objects
│   │   └── events.py           # domain events (created but not queued in Phase 1)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db.py               # SQLAlchemy engine/session factory
│   │   ├── qdrant_client.py    # Qdrant client singleton + helpers
│   │   ├── minio_client.py     # MinIO client singleton + helpers
│   │   ├── model_registry.py   # MODEL_MANIFEST loader
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── image_validator.py
│   │       ├── detector_adapter.py
│   │       ├── aligner_preprocessor.py
│   │       ├── recognizer_adapter.py
│   │       └── pipelines.py    # FacePipeline, EnrollmentPipeline, OnlineIdentifyPipeline
│   └── repositories/
│       ├── __init__.py
│       ├── person_repo.py
│       ├── photo_repo.py
│       ├── face_sample_repo.py
│       ├── identification_request_repo.py
│       └── audit_repo.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                    # generated in Phase 1B
├── pyproject.toml
└── Dockerfile
```

## How others implement this

The `fastapi/full-stack-fastapi-template` project is a widely-used reference. Its backend uses:

- `backend/app/api/` for routers grouped by domain (`users.py`, `items.py`, `login.py`).
- `backend/app/api/deps.py` for reusable FastAPI dependencies (`SessionDep`, `CurrentUser`).
- `backend/app/core/config.py` for Pydantic-based settings loaded from `.env`.
- `backend/app/crud.py` for database operations abstracted away from routers.
- `backend/app/models.py` for model/schema definitions (SQLModel in that template).
- `backend/app/alembic/` for migrations.

Request flow in that template: router → dependencies → CRUD service → model → database.

We do **not** copy SQLModel; MergenVision uses SQLAlchemy 2.0 ORM to keep explicit separation between persistence models and Pydantic API schemas.

## How MergenVision will adapt this

- **Routers (`app/api/v1/`)**: map exactly to the Phase 1 allowed routes in `API_CONTRACT.md`. No placeholder routes for `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams`.
- **Dependencies (`app/api/dependencies.py`)**: provide `AsyncSession`, `QdrantClient`, `Minio`, and model adapters via FastAPI `Depends`. No business logic in dependencies.
- **Application services (`app/application/`)**: own transactions, audit logging, and orchestration. Repositories are data-access-only; services are business-logic-only.
- **Domain models (`app/domain/`)**: define UUIDv7 identifiers, soft-delete (`isActive`/`deletedAt`), and value objects. Database models in `infrastructure/db.py` inherit from a shared `DeclarativeBase` and implement the persistence mapping.
- **Adapters (`app/infrastructure/adapters/`)**: implement the `MODEL_ADAPTER_BOUNDARY.md` contracts. `FacePipeline` is an ML orchestrator, not a business service.
- **Config (`app/core/config.py`)**: environment-driven; includes PostgreSQL, Qdrant, MinIO, model manifest path, and GPU runtime flags. Never hardcodes model binaries or GPU UUIDs.
- **Lifespan**: create long-lived Qdrant, MinIO, and model-adapter instances on startup; close them on shutdown.

## Files to be created in later phases

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/api/dependencies.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/people.py`, `photos.py`, `identify.py`, `identification_requests.py`, `audit.py`, `stats.py`, `media.py`
- `backend/app/application/*_service.py`
- `backend/app/domain/models.py`
- `backend/app/repositories/*_repo.py`
- `backend/app/infrastructure/db.py`, `qdrant_client.py`, `minio_client.py`, `model_registry.py`
- `backend/app/infrastructure/adapters/*.py`

## Risks and open items

- Deeply-nested packages increase import complexity; use absolute imports and a clear `__init__.py` policy.
- Async SQLAlchemy with greenlet requires careful fixture design; see `02_SQLALCHEMY_ALEMBIC_DATA_ACCESS.md`.
- Model adapter lifecycle must support hot-fallback from CUDA to CPU in demo mode; see `05_MODEL_ADAPTER_AND_INFERENCE_INTEGRATION.md`.
