# Phase 1B Backend Foundation Report

> **Scope lock:** This report covers only the Phase 1B foundation slice. No business routes, database models, migrations, Docker files, model adapters, Qdrant/MinIO clients, or placeholder future routes were added.

## What changed

Created the backend foundation for the MergenVision Phase 1 photo-based person-recognition platform:

- `backend/pyproject.toml` — project metadata, pinned runtime/dev dependencies, `ruff`, `mypy`, and `pytest` configuration.
- `backend/app/main.py` — FastAPI app factory (`create_app`) with `lifespan` async context manager.
- `backend/app/core/config.py` — `pydantic-settings` driven configuration with `.env` support and `extra="ignore"`.
- `backend/app/core/logging.py` — standard structured logging setup.
- `backend/app/core/errors.py` — domain exception hierarchy (`MergenVisionError`, `NotFoundError`, `ConflictError`, `ValidationError`) and status-code mapping.
- `backend/app/core/security.py` — request-ID tracing and header sanitization helpers.
- `backend/app/core/ids.py` — pure-Python UUIDv7 generator compatible with Python 3.12.
- `backend/app/api/v1/router.py` and `health.py` — root-level `/health` and `/ready` endpoints.
- `backend/app/api/dependencies.py` — `get_db` and `get_readiness_service` dependency factories.
- `backend/app/application/readiness_service.py` — readiness orchestration service.
- `backend/app/infrastructure/db.py` — SQLAlchemy 2.0 async `DeclarativeBase`, engine, and session factory.
- `backend/app/infrastructure/health_checks.py` — abstract `HealthCheck`, PostgreSQL check, and placeholder checks for future Qdrant/MinIO wiring.
- `backend/app/schemas/health.py` — `/health` and `/ready` response schemas.
- `backend/tests/conftest.py` — session-scoped app and async HTTP client fixtures.
- `backend/tests/api/test_health_ready.py` — `/health` and `/ready` contract tests.
- `backend/tests/api/test_openapi_scope.py` — verifies OpenAPI exposes only `/health` and `/ready`.
- `backend/tests/unit/test_config.py` — settings defaults and caching test.
- `backend/tests/unit/test_ids.py` — UUIDv7 generation and parsing tests.

## Key decisions

- **Root-level routes:** `/health` and `/ready` are registered without any `/api/v1` runtime prefix, per `API_CONTRACT.md`.
- **No placeholder future routes:** `/videos/*`, `/imports/*`, `/faces/*`, `/oracle/*`, `/objects/*`, `/streams/*` and 501 stubs are absent.
- **Layered separation:** routers are thin; readiness logic lives in `application/readiness_service.py`.
- **UUIDv7:** implemented locally because Python 3.12 lacks `uuid.uuid7()`; no extra dependency required.
- **Async SQLAlchemy 2.0:** `create_async_engine` + `async_sessionmaker` + `DeclarativeBase`.
- **Scope-safe config:** Qdrant/MinIO checks are placeholders (`SimpleHealthCheck`) until their clients are implemented in later slices.

## Verification

```bash
cd backend
source .venv/bin/activate
pytest -q                        # 7 passed
ruff check app tests             # All checks passed
ruff format --check app tests    # 28 files already formatted
mypy app                         # Success: no issues found in 20 source files
```

Additional grep checks performed on `backend/app`:

- No forbidden routes (`/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams`, `501`)
- No forbidden Phase 1 tables (`video_job`, `video_track`, `import_job`, etc.)
- No `/api/v1` router prefix

Git status shows only `backend/` as untracked; no modifications to governance/architecture docs.

## Unverified assumptions

- The default `DATABASE_URL` assumes PostgreSQL with `asyncpg`, but no real database is required for the current tests.
- Future Qdrant/MinIO readiness checks will replace the placeholder `SimpleHealthCheck` instances when those clients are added.
