# 06 Service Layer and Domain Model

> **Reference-first sources:** `docs/architecture/API_CONTRACT.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`, `docs/architecture/SENSITIVE_DATA_RULES.md`, `docs/architecture/FUTURE_BOUNDARIES.md`.

## Goal

Define the domain entities, value objects, and application services that implement the Phase 1 use cases while keeping ML orchestration inside the adapter boundary.

## Domain model (value objects and entities)

```python
class PersonId: UUID
class PhotoId: UUID
class SampleId: UUID
class RequestId: UUID
class QueryFaceId: UUID
class ResultId: UUID

class Person:
    personId: UUID
    displayName: str | None
    metadata: dict | None  # non-sensitive tags only
    isActive: bool
    createdAt: datetime
    updatedAt: datetime

class PersonPhoto:
    photoId: UUID
    personId: UUID
    bucket: str
    objectKey: str
    contentType: str
    sizeBytes: int
    width: int
    height: int
    isActive: bool

class FaceSample:
    sampleId: UUID
    personId: UUID
    photoId: UUID
    qdrantPointId: UUID
    collectionName: str
    modelName: str
    modelVersion: str
    embeddingDimension: int
    isActive: bool

class IdentificationRequest:
    requestId: UUID
    status: RequestStatus  # pending / completed / failed
    topK: int
    threshold: float | None
    createdAt: datetime
    completedAt: datetime | None

class IdentificationQueryFace:
    queryFaceId: UUID
    requestId: UUID
    bucket: str | None
    objectKey: str | None

class IdentificationResult:
    resultId: UUID
    requestId: UUID
    personId: UUID
    sampleId: UUID
    score: float
    rank: int
```

## How others implement this

Layered FastAPI projects typically separate:

- **Domain models**: plain Python classes or Pydantic models representing business concepts, independent of persistence.
- **Schemas**: Pydantic models used for request/response validation.
- **Services**: stateless classes that orchestrate repositories, external clients, and domain rules.
- **Repositories**: abstract data access; one per aggregate.

The service layer owns transactions and audit logging, while repositories remain persistence-agnostic aside from SQLAlchemy specifics.

## How MergenVision will adapt this

- **Domain package** (`app/domain/models.py`): immutable/value objects with UUIDv7 constructors. No SQLAlchemy imports.
- **Application services** (`app/application/`):
  - `PeopleService`: create/update/delete person, list/filter.
  - `PhotoService`: upload photo → trigger `EnrollmentPipeline` → create `person_photo` + `face_sample` + Qdrant point.
  - `IdentifyService`: receive query image → trigger `OnlineIdentifyPipeline` → search Qdrant → resolve candidates → store request/query/results.
  - `AuditService`: append `audit_log` rows; includes safe metadata only.
  - `StatsService`: read-only counters from PostgreSQL and Qdrant.
- **Service responsibilities**:
  - Validate business rules (e.g., max photos per person, allowed image types).
  - Coordinate repository writes and Qdrant/MinIO side effects.
  - Write audit records near the commit boundary.
  - Convert domain results to Pydantic response schemas.
- **What services do NOT do**:
  - Decode or preprocess images (done by adapters).
  - Run ONNX inference directly (done by adapters).
  - Hardcode model paths or GPU indices.
- **Transaction boundaries**: one service method = one logical transaction. If Qdrant upsert fails after PostgreSQL insert, raise an exception so the DB transaction rolls back; later Phase 1C may add compensating retry logic.
- **Audit requirements**: every mutating operation (`POST`, `PATCH`, `DELETE`) produces an `audit_log` row with `action`, `actor`, `entityType`, `entityId`, `requestId`, and a metadata summary free of PII/vectors/images.

## Files to be created in later phases

- `backend/app/domain/models.py`
- `backend/app/application/people_service.py`
- `backend/app/application/photo_service.py`
- `backend/app/application/identify_service.py`
- `backend/app/application/audit_service.py`
- `backend/app/application/stats_service.py`

## Verification plan

- Unit tests for services using in-memory repositories and mocked adapters.
- Integration tests for `PhotoService` and `IdentifyService` against PostgreSQL + Qdrant + MinIO test containers.
