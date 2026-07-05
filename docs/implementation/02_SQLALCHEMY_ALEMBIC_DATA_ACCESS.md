# 02 SQLAlchemy and Alembic Data Access

> **Reference-first sources:** `docs/architecture/DATA_MODEL.md`, `docs/architecture/SENSITIVE_DATA_RULES.md`, `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`, Context7 (SQLAlchemy, Alembic), deepwiki `sqlalchemy/sqlalchemy`.

## Goal

Define PostgreSQL persistence using SQLAlchemy 2.0 and Alembic, scoped to the Phase 1 allowed tables, enforcing the data-ownership rule: PostgreSQL owns business metadata, history, results, and audit logs; it never stores raw embedding vectors or image bytes.

## Phase 1 allowed tables

- `person`
- `person_photo`
- `face_sample`
- `identification_request`
- `identification_query_face`
- `identification_result`
- `audit_log`

Forbidden in Phase 1: `video_job`, `video_track`, `face_video_appearance`, `import_job`, `import_job_item`, `anonymous_face`, `face_identity`, `object_detection_job`.

## Identifier rule

All primary keys use UUIDv7: `personId`, `photoId`, `sampleId`, `requestId`, `queryFaceId`, `resultId`, `auditId`.

## How others implement this

The `sqlalchemy/sqlalchemy` project recommends SQLAlchemy 2.0 patterns:

- Base class inherits from `sqlalchemy.orm.DeclarativeBase`.
- Models use `Mapped[T]` and `mapped_column(...)`.
- Async applications use `create_async_engine` and `async_sessionmaker` from `sqlalchemy.ext.asyncio`.
- A FastAPI dependency yields `AsyncSession` instances per request:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

async_engine = create_async_engine("postgresql+asyncpg://...")
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- Repository classes accept an `AsyncSession` and encapsulate queries; e.g.:

```python
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int):
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
```

- Alembic migration workflow:
  1. `alembic revision --autogenerate -m "message"`
  2. Review generated migration.
  3. `alembic upgrade head`

- In async Alembic `env.py`, use `run_async_migrations` and pass an `AsyncEngine` to `context.configure`.

## How MergenVision will adapt this

- **Async PostgreSQL driver**: `asyncpg` with `postgresql+asyncpg://`. Sync fallback reserved for offline admin scripts and migration generation.
- **Base model** (`app/infrastructure/db.py`):

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SoftDeleteMixin:
    isActive: Mapped[bool] = mapped_column(default=True)
    deletedAt: Mapped[datetime | None] = mapped_column(nullable=True)
```

- **Models**: each table maps to a class with UUIDv7 primary key. `face_sample` stores `modelName`, `modelVersion`, `embeddingDimension`, and `qdrantPointId`/`collectionName` references, but **never** the embedding vector itself.
- **Repositories** (`app/repositories/`): async classes per aggregate. Each repository uses `AsyncSession` only. No repository calls Qdrant or MinIO directly; those are injected at the service level.
- **Unit of work**: service layer coordinates repository commits and audit writes in a single request-scoped transaction. Audit logging uses an `audit_repo` inserted within the same transaction when possible; for failures outside transactions, a separate resilient audit path is defined.
- **Alembic**:
  - Init with `alembic init alembic` in Phase 1B.
  - `env.py` points to async engine and metadata.
  - Autogenerate migrations; no hand-written DDL unless required by a data-migration.
  - Migration file naming: `YYYYMMDDHHMMSS_<name>.py`.

## Sensitive-data rules

- Never store raw national ID or full date-of-birth if not required by API contract.
- Never store image bytes, base64, or embeddings in PostgreSQL.
- Audit log stores action type, entity IDs, request ID, and safe metadata; never raw images, vectors, or full person details.

## Files to be created in later phases

- `backend/app/infrastructure/db.py`
- `backend/app/models/` (if package split is chosen) or persistence models co-located in repositories
- `backend/app/repositories/person_repo.py`
- `backend/app/repositories/photo_repo.py`
- `backend/app/repositories/face_sample_repo.py`
- `backend/app/repositories/identification_request_repo.py`
- `backend/app/repositories/audit_repo.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/*.py`

## Verification plan

- Run `alembic upgrade head` against a fresh PostgreSQL container.
- Run `alembic downgrade -1` and `alembic upgrade head` to confirm reversibility.
- Verify all Phase 1 tables exist and forbidden tables do not.
