# MergenVision — API Contract (Phase 1)

> Base path: `/api/v1` (or root mounting per deployment).  
> All IDs are UUIDv7.  
> All timestamps are ISO-8601 UTC.

## Allowed Phase 1 Endpoints

```text
GET  /health
GET  /ready

POST /people
GET  /people
GET  /people/{personId}
PATCH /people/{personId}
DELETE /people/{personId}

POST /people/{personId}/photos
GET  /people/{personId}/photos
DELETE /people/{personId}/photos/{photoId}

POST /identify
GET  /identification-requests
GET  /identification-requests/{requestId}

GET  /audit
GET  /stats

GET  /media/{bucket}/{objectKey}
```

## Common Response Patterns

- Listings return `{items, total, limit, offset}`.
- Errors return `{detail: string}` with appropriate HTTP status.
- IDs exposed as path/query parameters without national ID.

## People

### POST /people

Create a person.

**Request body:**

```json
{
  "firstName": "Barış",
  "lastName": "Özcan",
  "nationalId": "12345678901",
  "details": { "department": "Engineering" }
}
```

**Response 201:**

```json
{
  "personId": "uuid",
  "firstName": "Barış",
  "lastName": "Özcan",
  "nationalIdMasked": "******8901",
  "details": { "department": "Engineering" },
  "isActive": true,
  "createdAt": "...",
  "updatedAt": "..."
}
```

### GET /people

List active people.

**Query:** `limit` (1-100, default 20), `offset` (≥0, default 0).

**Response 200:**

```json
{
  "items": [ { ...person response... } ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### GET /people/{personId}

Get a single active person.

### PATCH /people/{personId}

Update a person. Only provided fields are updated.

### DELETE /people/{personId}

Soft-delete a person and cascade-soft-delete their photos/samples.

## Photos & Enrollment

### POST /people/{personId}/photos

Upload a photo and enroll the best face.

**Request:** multipart/form-data with `image` file (JPEG/PNG, max 10 MiB).

**Response 201:**

```json
{
  "photoId": "uuid",
  "personId": "uuid",
  "faceId": "uuid",
  "sampleId": "uuid",
  "qdrantPointId": "uuid",
  "imageUrl": "/media/people-photos/uuid/uuid/original.jpg",
  "cropImageUrl": "/media/face-crops/uuid/uuid/crop.jpg",
  "modelName": "arcface_w600k_r50_batch",
  "modelVersion": "batch",
  "embeddingDimension": 512,
  "qualityScore": 0.94,
  "isIndexed": true,
  "createdAt": "..."
}
```

**Errors:**
- `400` no face detected.
- `400` multiple faces detected (Phase 1 rejects group photos for enrollment).
- `404` person not found.
- `413` file too large.

### GET /people/{personId}/photos

List active photos for a person.

### DELETE /people/{personId}/photos/{photoId}

Soft-delete a photo and de-index its sample from Qdrant.

## Identification

### POST /identify

Identify faces in an image.

**Query params:**
- `topK` (int, 1-20, default 5)
- `selectedFaceIndex` (int, optional): if multiple faces, identify only this one (0-based).
- `threshold` (float, optional): override default thresholds.

**Request:** multipart/form-data with `image` file.

**Response 200:**

```json
{
  "requestId": "uuid",
  "status": "completed",
  "decision": "single_face",
  "faceCount": 1,
  "queryImageUrl": "/media/query-images/uuid/query.jpg",
  "faces": [
    {
      "queryFaceId": "uuid",
      "boundingBox": { "x": 100, "y": 80, "width": 120, "height": 120 },
      "qualityScore": 0.92,
      "result": {
        "status": "matched",
        "personId": "uuid",
        "faceId": "uuid",
        "sampleId": "uuid",
        "name": "Barış Özcan",
        "score": 0.73,
        "threshold": 0.60
      },
      "candidates": [
        { "rank": 1, "faceId": "uuid", "personId": "uuid", "sampleId": "uuid", "name": "Barış Özcan", "score": 0.73, "decision": "matched" },
        { "rank": 2, "faceId": "uuid", "personId": "uuid", "sampleId": "uuid", "name": "Ali Veli", "score": 0.45, "decision": "possible_match" }
      ]
    }
  ]
}
```

**Decision rules:**
- `score ≥ matched_threshold` → `matched`
- `possible_match_threshold ≤ score < matched_threshold` → `possible_match`
- `score < possible_match_threshold` → `no_match`
- No face → `decision: no_face`, `faceCount: 0`
- Multiple faces → `decision: multiple_faces`, `faceCount: N`

Default thresholds: `matched=0.6`, `possible_match=0.4`.

### GET /identification-requests

List identification requests (newest first).

**Response 200:**

```json
{
  "items": [ { ...identification response summary... } ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

### GET /identification-requests/{requestId}

Get full identification request result.

## Audit

### GET /audit

Query audit log.

**Query params:** `entityType`, `entityId`, `action`, `limit`, `offset`.

**Response 200:** paginated list of audit entries (no PII/embeddings).

## Stats

### GET /stats

**Response 200:**

```json
{
  "personCount": 1000,
  "photoCount": 1200,
  "faceSampleCount": 1200,
  "identificationRequestCount": 5400
}
```

## Media

### GET /media/{bucket}/{objectKey}

Return a presigned redirect or the object bytes. Response content type matches the stored object.

## Health

### GET /health

Liveness probe. Returns `{"status": "ok"}`.

### GET /ready

Readiness probe. Checks PostgreSQL, Qdrant, MinIO, TensorRT runtime loaded. Returns `{"status": "ready"}` or `503`.

## Errors

Common HTTP status codes:

| Status | Meaning |
|---|---|
| 400 | Validation / no face / multiple faces / bad input |
| 404 | Resource not found |
| 409 | Conflict (duplicate national ID) |
| 413 | Payload too large |
| 422 | Unprocessable entity (schema violation) |
| 503 | Service unavailable (engine missing, dependency down) |
| 500 | Internal server error |
