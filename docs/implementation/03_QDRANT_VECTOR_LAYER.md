# 03 Qdrant Vector Layer

> **Reference-first sources:** `docs/architecture/DATA_MODEL.md`, `docs/architecture/MODEL_ADAPTER_BOUNDARY.md`, `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`, Context7 (Qdrant), deepwiki `qdrant/qdrant`.

## Goal

Use Qdrant as the vector store for face embeddings. Qdrant owns vectors and reference-only payloads; it never owns sensitive person metadata or image bytes.

## How others implement this

The `qdrant/qdrant` Python-client patterns (derived from test utilities and documentation) recommend:

- Initialize `QdrantClient` once and reuse it. In FastAPI, attach it to `app.state` in lifespan events.

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333, timeout=60)
```

- Create collections with explicit `VectorParams`:

```python
from qdrant_client import models

client.create_collection(
    collection_name="items",
    vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE),
)
```

- Upsert in batches using `models.PointStruct`:

```python
points = [
    models.PointStruct(id=str(uuid.uuid4()), vector=vec, payload=payload)
    for vec, payload in zip(vectors, payloads)
]
client.upsert(collection_name="items", points=points, wait=True)
```

- Search with payload filters using `models.Filter` and `models.FieldCondition`:

```python
results = client.query_points(
    collection_name="items",
    query=query_vector,
    limit=10,
    query_filter=models.Filter(
        must=[models.FieldCondition(key="isActive", match=models.MatchValue(value=True))]
    ),
)
```

- For multiple embedding models, use collection names that encode model name/version, e.g. `face_arcface_r50_w600k_512d_v1`.

## How MergenVision will adapt this

- **Client lifecycle**: long-lived `QdrantClient` created in `app/infrastructure/qdrant_client.py` at startup. Async sync is not natively required; blocking calls run in `asyncio.to_thread` if needed.
- **Collection naming strategy**: one collection per recognizer model and version, with explicit dimension and distance metric. Example:
  - `face_arcface_r50_w600k_512d_v1` → ArcFace r50, output 512-D.
  - Future collections for other models get distinct names and dimensions.
- **Payload restrictions**: payload contains only `personId`, `sampleId`, `photoId`, `isActive`, `modelName`, `modelVersion`, `createdAt`. No raw national ID, no names, no image bytes, no full metadata.
- **Point id**: use the same UUIDv7 as the corresponding `face_sample.sampleId` for deterministic mapping.
- **Search semantics**:
  - Identification: query against active points in the model-specific collection, `limit = topK` from request.
  - Payload filter: `isActive == True` always applied; soft-deleted samples are excluded.
  - Result includes `score`, `personId`, `sampleId`, `photoId`; service layer resolves person identity from PostgreSQL.
- **Collection creation idempotency**: a startup check creates the target collection if it does not exist, using `VectorParams` from `MODEL_MANIFEST.json` for the active recognizer.
- **Batch support**: `EnrollmentPipeline` returns a list of `(sampleId, vector, payload)` tuples; service layer calls `client.upsert` in batches ≤ `QDRANT_UPSERT_BATCH_SIZE`.

## Files to be created in later phases

- `backend/app/infrastructure/qdrant_client.py`
- `backend/app/infrastructure/vector_store.py` (optional wrapper around client)
- `backend/app/application/identify_service.py` (calls Qdrant)
- `backend/app/infrastructure/adapters/recognizer_adapter.py` (produces vectors)

## Verification plan

- Unit tests patch `QdrantClient` methods.
- Integration tests run a local Qdrant container:
  - create collection,
  - upsert points,
  - search with active/inactive filter,
  - verify payload contains no sensitive fields.
