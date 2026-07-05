# 09 Testing and Quality Strategy

> **Reference-first sources:** `docs/architecture/SELF_REVIEW_AND_VERIFICATION_POLICY.md`, `docs/architecture/PHASE_IMPLEMENTATION_GATES.md`, Context7 (pytest), deepwiki `pytest-dev/pytest`.

## Goal

Define a test pyramid and quality gates for Phase 1 that verify the platform without running real-image benchmarks or LFW in the planning phase.

## Test pyramid

```text
        /\
       /  \  E2E smoke (containers + real ONNX CPU)
      /____\       5%
     /      \  Integration (repos + Qdrant + MinIO)
    /________\     25%
   /          \  Unit (services, adapters with mocks)
  /____________\   70%
```

## How others implement this

The `pytest-dev/pytest` project recommends:

- Tests live in a top-level `tests/` directory mirroring the app structure.
- Use fixtures for database and external service setup/teardown.
- Use `monkeypatch` to replace module attributes or config values.
- Use `pytest-asyncio` for async tests and fixtures.
- FastAPI testing integrates cleanly with `TestClient` fixtures.
- The `pytest-fastapi-deps` plugin can replace FastAPI dependencies during tests.

Example fixture pattern:

```python
@pytest.fixture(scope="session")
def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session
```

## How MergenVision will adapt this

- **Framework**: `pytest` + `pytest-asyncio` + `httpx` (for `TestClient` with async apps).
- **Directory**: `backend/tests/`
  - `unit/` — pure logic, domain models, adapter preprocessing, service rules.
  - `integration/` — repositories with test PostgreSQL, Qdrant/MinIO clients with real containers.
  - `e2e/` — full FastAPI app + containers + ONNX CPU model smoke tests.
- **Fixtures**:
  - `async_postgres`: starts a PostgreSQL test container, runs migrations.
  - `async_db_session`: yields `AsyncSession` bound to the test DB.
  - `qdrant_client`: starts a Qdrant test container.
  - `minio_client`: starts a MinIO test container.
  - `test_app`: FastAPI app override with test dependencies.
  - `client`: `TestClient(test_app)`.
  - `fake_adapters`: deterministic detector/recognizer returning fixed outputs.
- **Unit tests**:
  - Image validator rejects oversized/non-image files.
  - `EnrollmentPipeline` produces expected `FaceSample` domain objects.
  - `IdentifyService` aggregates Qdrant hits into ranked candidates.
- **Integration tests**:
  - Person/photo CRUD roundtrip.
  - Upload photo → face sample → Qdrant point.
  - Identify against enrolled sample returns correct person.
  - Presigned media URL fetches the correct object.
- **E2E smoke tests**:
  - Start the app with real ONNX models on CPU.
  - Call `/health`, `/ready`, `/people`, `/people/{id}/photos`, `/identify`.
  - No assertions on accuracy; only verify the pipeline runs end-to-end without errors.
- **Quality gates**:
  - `ruff` lint/format.
  - `mypy` type check.
  - All tests pass on CPU before any GPU demo.
  - Branch coverage ≥ 80% for services and adapters.

## What is NOT in Phase 1A/1B testing

- LFW benchmark.
- Real-image accuracy thresholds.
- Stress/load tests.
- Multi-GPU concurrency benchmarks.
- Security penetration tests.

## Files to be created in later phases

- `backend/pyproject.toml`
- `backend/tests/conftest.py`
- `backend/tests/unit/test_*.py`
- `backend/tests/integration/test_*.py`
- `backend/tests/e2e/test_*.py`
- CI workflow (optional, in `.github/workflows/`)

## Verification plan

- `pytest -q` passes with all fixtures.
- `ruff check backend/app backend/tests`
- `mypy backend/app`
- Coverage report shows ≥ 80% on service and adapter modules.
