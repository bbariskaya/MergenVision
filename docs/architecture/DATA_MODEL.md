# MergenVision — Data Model

> Phase 1 allowed tables only. Phase 2/3 tables are listed in Future Boundaries.

## Ownership Rules

- **PostgreSQL** owns business metadata, identity relationships, request history, audit logs, and future video job metadata.
- **Qdrant** owns vector embeddings and reference-only payload.
- **MinIO** owns image bytes, videos, query images, and frame crops.

Never store in Qdrant: raw national ID, full person details, sensitive metadata, image bytes.
Never store in audit: raw national ID, image bytes/base64, embeddings, full sensitive person details.
Never store in PostgreSQL: raw embedding vectors, image bytes.

## Phase 1 Allowed Tables

```text
person
person_photo
face_identity
face_sample
identification_request
identification_query_face
identification_result
audit_log
```

## Entity Definitions

### person

A unique known identity in the shared platform.

| Column | Type | Notes |
|---|---|---|
| personId | UUIDv7 PK | |
| firstName | string nullable | |
| lastName | string nullable | |
| nationalIdHash | string nullable unique index | bcrypt/argon2 hash of national ID |
| nationalIdMasked | string nullable | e.g. `******8901` |
| details | JSONB nullable | extensible fields (department, oracle id, etc.) |
| isActive | bool | soft delete flag |
| deletedAt | timestamptz nullable | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### person_photo

A stored original photo for a known person.

| Column | Type | Notes |
|---|---|---|
| photoId | UUIDv7 PK | |
| personId | UUID FK → person | |
| originalImageBucket | string | MinIO bucket |
| originalImageKey | string | MinIO object key |
| contentType | string | image/jpeg or image/png |
| sizeBytes | int | |
| width | int nullable | |
| height | int nullable | |
| isActive | bool | soft delete |
| deletedAt | timestamptz nullable | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### face_identity

Stable face-level identity used across photo, video, and live phases. Phase 1 only uses `identityType = known`. Phase 2 adds `anonymous` rows.

| Column | Type | Notes |
|---|---|---|
| faceId | UUIDv7 PK | stable face identity |
| identityType | enum `known` / `anonymous` | Phase 1: `known` only |
| personId | UUID FK → person nullable | null for anonymous faces |
| displayName | string nullable | person name or anonymous label |
| isActive | bool | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### face_sample

A reference face sample (embedding source) linked to a `face_identity` and a Qdrant vector point.

| Column | Type | Notes |
|---|---|---|
| sampleId | UUIDv7 PK | |
| faceId | UUID FK → face_identity | stable identity of this sample |
| photoId | UUID FK → person_photo | nullable if sample does not come from a photo |
| qdrantPointId | UUID | UUID of the matching Qdrant point |
| collectionName | string | Qdrant collection the point lives in |
| modelName | string | e.g. `arcface_w600k_r50_batch` |
| modelVersion | string | e.g. `batch` |
| embeddingDimension | int | 512 |
| qualityScore | float nullable | detector confidence or quality metric |
| cropImageBucket | string nullable | MinIO bucket for the face crop |
| cropImageKey | string nullable | MinIO object key for the crop |
| isIndexed | bool | false until Qdrant upsert succeeds |
| isActive | bool | soft delete |
| deletedAt | timestamptz nullable | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### identification_request

A single identification request.

| Column | Type | Notes |
|---|---|---|
| requestId | UUIDv7 PK | |
| status | string | pending / processing / completed / failed |
| decision | string nullable | no_face / single_face / multiple_faces / matched / possible_match / no_match |
| faceCount | int nullable | number of faces detected |
| topK | int | search candidate count |
| threshold | float nullable | optional client override |
| queryImageBucket | string nullable | MinIO bucket for query image |
| queryImageKey | string nullable | MinIO object key for query image |
| completedAt | timestamptz nullable | |
| errorMessage | string nullable | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### identification_query_face

A face detected inside an identification request.

| Column | Type | Notes |
|---|---|---|
| queryFaceId | UUIDv7 PK | |
| requestId | UUID FK → identification_request | |
| boundingBox | JSONB | `{x, y, width, height}` in original image coordinates |
| landmarks | JSONB | optional 5-point landmarks |
| qualityScore | float nullable | |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### identification_result

A ranked candidate result for a query face.

| Column | Type | Notes |
|---|---|---|
| resultId | UUIDv7 PK | |
| requestId | UUID FK → identification_request | |
| queryFaceId | UUID FK → identification_query_face | |
| faceId | UUID FK → face_identity nullable | matched identity |
| sampleId | UUID FK → face_sample nullable | best matching sample |
| personId | UUID FK → person nullable | matched person (if known) |
| score | float | cosine similarity or normalized distance |
| rank | int | 1-based rank |
| decision | string | matched / possible_match / no_match |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

### audit_log

Safe audit trail for mutating operations.

| Column | Type | Notes |
|---|---|---|
| auditId | UUIDv7 PK | |
| action | string | e.g. `person:create`, `photo:enroll`, `identify` |
| entityType | string | e.g. `person`, `person_photo`, `face_sample` |
| entityId | UUID nullable | |
| actor | string nullable | api / user / worker |
| requestId | UUID nullable | correlation id |
| outcome | string | success / failure |
| safeMetadata | JSONB | scalar metadata only; no PII/embeddings/images |
| createdAt | timestamptz | |
| updatedAt | timestamptz | |

## Indexes

- `person`: `nationalIdHash` unique, `isActive`.
- `person_photo`: composite `(personId, isActive)`.
- `face_identity`: `(personId)`, `(identityType, isActive)`.
- `face_sample`: `(faceId, isActive)`, `(collectionName, isIndexed)`.
- `identification_request`: `(createdAt)`.
- `identification_result`: `(requestId, rank)`.
- `audit_log`: `(createdAt)`, `(entityType, entityId)`.

## Qdrant Collection Schema

Collection name pattern:

```text
face_samples_<modelName>_<embeddingDimension>_<modelVersion>
```

Example: `face_samples_arcface_w600k_r50_batch_512_batch`

Distance metric: `cosine`.

Payload (reference only):

```json
{
  "faceId": "uuid",
  "personId": "uuid",
  "photoId": "uuid",
  "sampleId": "uuid",
  "identityType": "known",
  "modelName": "arcface_w600k_r50_batch",
  "modelVersion": "batch",
  "embeddingDimension": 512,
  "isActive": true
}
```

Payload indexes: `faceId`, `personId`, `photoId`, `identityType`, `isActive`.

## Future Tables (Phase 2 / Phase 3)

```text
video_job
video_track
face_video_appearance
import_job
import_job_item
anonymous_face          -- superseded by face_identity.identityType='anonymous'
object_detection_job
live_stream_job
stream_track
```

These are out of scope for Phase 1. They will reuse the same PostgreSQL/Qdrant/MinIO services.
