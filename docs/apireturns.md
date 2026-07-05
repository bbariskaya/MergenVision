# MergenVision — API Returns Reference (Phase 1)

> Derived from [`docs/architecture/API_CONTRACT.md`](./architecture/API_CONTRACT.md).  
> Base path: `/api/v1`. All IDs are UUIDv7 strings. Timestamps are ISO-8601 UTC.

This document is intended for UI/UX development. It lists every Phase 1 endpoint
with its request shape and a concrete JSON response example.

---

## Common Patterns

- **List response** shape:

  ```json
  {
    "items": [...],
    "total": 100,
    "limit": 20,
    "offset": 0
  }
  ```

- **Error response** shape:

  ```json
  { "detail": "Human-readable error message" }
  ```

- **Media URL** pattern: `/media/{bucket}/{objectKey}` returns the stored object
  bytes or a presigned redirect.

---

## Health

### `GET /health`

Liveness probe.

**Response 200:**

```json
{ "status": "ok" }
```

### `GET /ready`

Readiness probe. Returns `503` if PostgreSQL, Qdrant, MinIO, or the TensorRT
runtime is not ready.

**Response 200:**

```json
{ "status": "ready" }
```

---

## People

### `POST /people`

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
  "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
  "firstName": "Barış",
  "lastName": "Özcan",
  "nationalIdMasked": "******8901",
  "details": { "department": "Engineering" },
  "isActive": true,
  "createdAt": "2026-07-04T10:00:00Z",
  "updatedAt": "2026-07-04T10:00:00Z"
}
```

### `GET /people`

List active people.

**Query params:** `limit` (1-100, default 20), `offset` (≥0, default 0).

**Response 200:**

```json
{
  "items": [
    {
      "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
      "firstName": "Barış",
      "lastName": "Özcan",
      "nationalIdMasked": "******8901",
      "details": { "department": "Engineering" },
      "isActive": true,
      "createdAt": "2026-07-04T10:00:00Z",
      "updatedAt": "2026-07-04T10:00:00Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### `GET /people/{personId}`

Get a single active person.

**Response 200:** same shape as the item in `POST /people`.

### `PATCH /people/{personId}`

Update a person. Only provided fields are changed.

**Request body (example):**

```json
{
  "firstName": "Barış",
  "details": { "department": "Product" }
}
```

**Response 200:** full person object.

### `DELETE /people/{personId}`

Soft-delete a person and cascade-soft-delete their photos and face samples.

**Response 204:** no body.

---

## Photos & Enrollment

### `POST /people/{personId}/photos`

Upload a photo and enroll exactly one face. Rejected if zero or multiple faces
are detected.

**Request:** `multipart/form-data` with an `image` file (JPEG/PNG, max 10 MiB).

**Response 201:**

```json
{
  "photoId": "018f3b26-8b2d-8e7f-9c4d-37b2d8e7f9c4",
  "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
  "faceId": "018f3b26-9c3e-9f80-ad5e-48c3e9f80ad5",
  "sampleId": "018f3b26-ad4f-a091-be6f-59d4fa091be6",
  "qdrantPointId": "018f3b26-be50-b1a2-cf70-60e50b1a2cf7",
  "imageUrl": "/media/people-photos/018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b/018f3b26-8b2d-8e7f-9c4d-37b2d8e7f9c4/original.jpg",
  "cropImageUrl": "/media/face-crops/018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b/018f3b26-ad4f-a091-be6f-59d4fa091be6/crop.jpg",
  "modelName": "arcface_w600k_r50_batch",
  "modelVersion": "batch",
  "embeddingDimension": 512,
  "qualityScore": 0.94,
  "isIndexed": true,
  "createdAt": "2026-07-04T10:05:00Z"
}
```

Common errors:

- `400` — no face detected.
- `400` — multiple faces detected.
- `404` — person not found.
- `413` — file too large.

### `GET /people/{personId}/photos`

List active photos for a person.

**Response 200:**

```json
{
  "items": [
    {
      "photoId": "018f3b26-8b2d-8e7f-9c4d-37b2d8e7f9c4",
      "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
      "imageUrl": "/media/people-photos/018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b/018f3b26-8b2d-8e7f-9c4d-37b2d8e7f9c4/original.jpg",
      "originalImageBucket": "people-photos",
      "originalImageKey": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b/018f3b26-8b2d-8e7f-9c4d-37b2d8e7f9c4/original.jpg",
      "isActive": true,
      "createdAt": "2026-07-04T10:05:00Z"
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### `DELETE /people/{personId}/photos/{photoId}`

Soft-delete a photo and de-index its face sample from Qdrant.

**Response 204:** no body.

---

## Identification

### `POST /identify`

Identify faces in an uploaded image.

**Query params:**

- `topK` — number of candidates per face (1-20, default 5).
- `selectedFaceIndex` — optional 0-based index to identify only one face.
- `threshold` — optional score override (default logic uses configured thresholds).

**Request:** `multipart/form-data` with an `image` file.

**Response 200:**

```json
{
  "requestId": "018f3b26-cf60-c2b3-d081-71f60c2b3d08",
  "status": "completed",
  "decision": "single_face",
  "faceCount": 1,
  "queryImageUrl": "/media/query-images/018f3b26-cf60-c2b3-d081-71f60c2b3d08/query.jpg",
  "faces": [
    {
      "queryFaceId": "018f3b26-d070-d3c4-e192-82g70d3c4e19",
      "boundingBox": { "x": 100, "y": 80, "width": 120, "height": 120 },
      "qualityScore": 0.92,
      "result": {
        "status": "matched",
        "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
        "faceId": "018f3b26-9c3e-9f80-ad5e-48c3e9f80ad5",
        "sampleId": "018f3b26-ad4f-a091-be6f-59d4fa091be6",
        "name": "Barış Özcan",
        "score": 0.73,
        "threshold": 0.60
      },
      "candidates": [
        {
          "rank": 1,
          "faceId": "018f3b26-9c3e-9f80-ad5e-48c3e9f80ad5",
          "personId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
          "sampleId": "018f3b26-ad4f-a091-be6f-59d4fa091be6",
          "name": "Barış Özcan",
          "score": 0.73,
          "decision": "matched"
        },
        {
          "rank": 2,
          "faceId": "018f3b27-0d4e-0a1b-1c2d-3e4f5a6b7c8d",
          "personId": "018f3b27-1e5f-1b2c-2d3e-4f5a6b7c8d9e",
          "sampleId": "018f3b27-2f60-2c3d-3e4f-5a6b7c8d9e0f",
          "name": "Ali Veli",
          "score": 0.45,
          "decision": "possible_match"
        }
      ]
    }
  ]
}
```

**Decision values and status rules:**

| Decision        | Meaning                                  |
|-----------------|------------------------------------------|
| `no_face`       | No face was detected. `faceCount: 0`     |
| `single_face`   | One face was detected and processed.     |
| `multiple_faces`| More than one face; `faceCount: N`       |

Candidate decision rules (default thresholds):

- `score ≥ matched_threshold` (default 0.6) → `matched`
- `possible_match_threshold ≤ score < matched_threshold` (0.4–0.6) → `possible_match`
- `score < possible_match_threshold` → `no_match`

### `GET /identification-requests`

List identification requests, newest first.

**Query params:** `limit`, `offset`.

**Response 200:**

```json
{
  "items": [
    {
      "requestId": "018f3b26-cf60-c2b3-d081-71f60c2b3d08",
      "status": "completed",
      "decision": "single_face",
      "faceCount": 1,
      "createdAt": "2026-07-04T10:10:00Z"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

### `GET /identification-requests/{requestId}`

Get the full result of a single identification request.

**Response 200:** same shape as `POST /identify`.

---

## Audit

### `GET /audit`

Query the audit log.

**Query params:** `entityType`, `entityId`, `action`, `limit`, `offset`.

**Response 200:**

```json
{
  "items": [
    {
      "auditId": "018f3b27-3g71-3d4e-4f5a-6b7c8d9e0f1a",
      "action": "person.created",
      "entityType": "person",
      "entityId": "018f3b26-7a1c-7d6e-8f3b-26a1c7d6ef3b",
      "actor": "anonymous",
      "metadata": {},
      "createdAt": "2026-07-04T10:00:00Z"
    }
  ],
  "total": 120,
  "limit": 20,
  "offset": 0
}
```

---

## Stats

### `GET /stats`

System counters.

**Response 200:**

```json
{
  "personCount": 1000,
  "photoCount": 1200,
  "faceSampleCount": 1200,
  "identificationRequestCount": 5400
}
```

---

## Media

### `GET /media/{bucket}/{objectKey}`

Serve a stored object (photo, face crop, or query image).

- Returns the object bytes or a presigned redirect.
- `Content-Type` matches the stored object.

---

## HTTP Status Codes

| Status | Meaning                                                    |
|--------|------------------------------------------------------------|
| `200`  | OK                                                         |
| `201`  | Created                                                    |
| `204`  | No content (soft-delete)                                   |
| `400`  | Validation error, no face, or multiple faces               |
| `404`  | Resource not found                                         |
| `409`  | Conflict (duplicate national ID)                           |
| `413`  | Payload too large                                          |
| `422`  | Schema violation                                           |
| `503`  | Service unavailable (engine missing or dependency down)    |
| `500`  | Internal server error                                      |
