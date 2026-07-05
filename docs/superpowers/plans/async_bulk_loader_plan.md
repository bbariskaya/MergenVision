# Async Bulk Dataset Loader Plan

## Goal
Write a high-throughput loader script that keeps the GPU fed at ~300 img/s by
decoupling inference from persistence. Persistence (DB, MinIO, Qdrant) happens
asynchronously after inference, overlapping with the next inference batch.

## Design
1. Add `PersonRepository.bulk_create()` for O(1) person inserts.
2. New script `backend/scripts/load_dataset_async.py`:
   * Parse dataset mapping:
     - `--dataset celeba`: `--identity-file identity_CelebA.txt`, `--images-dir img_align_celeba/`
     - `--dataset lfw`: `--lfw-dir lfw-deepfunneled/lfw-deepfunneled/`
   * Pre-create all persons with bulk inserts and map external identity id -> personId.
   * Producer: read image bytes + validate metadata in async chunks of N images.
   * Inference worker: run `FacePipeline.enroll_batch` in a single thread pool
task; push `(chunk, outputs)` to persistence queue.
   * Persistence worker(s):
     - bulk create `FaceIdentity` rows,
     - concurrently upload original photos + face crops to MinIO,
     - bulk create `PersonPhoto` and `FaceSample` rows,
     - bulk upsert Qdrant points,
     - commit session and log audit entry per chunk.
3. Use bounded `asyncio.Queue` between stages so inference of chunk N+1 overlaps
with persistence of chunk N.

## Files to change
* `backend/scripts/load_dataset_async.py` — new script
* `backend/app/repositories/person_repo.py` — add `bulk_create()`

## Verification
* Run on LFW subset (e.g. first 1,000 photos) inside `api-gpu-1`.
* Confirm `img/s` reported is closer to ML-only benchmark while still having
all rows in PG/Qdrant/MinIO.
* Check counts in dashboard or `/stats`.

## Constraints
* Phase 1 existing tables only (`person`, `person_photo`, `face_identity`, `face_sample`).
* No new API routes.
* UUIDv7 for new IDs.
* CelebA dataset must already be on local disk; no download.
