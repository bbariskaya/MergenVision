# 10 Security and PII Handling

> **Reference-first sources:** `docs/architecture/SENSITIVE_DATA_RULES.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/API_CONTRACT.md`, `docs/architecture/AUDIT_POLICY.md` (if present), `docs/architecture/PHASE_IMPLEMENTATION_GATES.md`.

## Goal

Document how Phase 1 protects sensitive person data, images, embeddings, and audit logs while keeping the platform usable for photo-based recognition.

## Data classification

| Data | Storage | Access control |
|------|---------|----------------|
| Person business metadata (name, tags) | PostgreSQL | API auth-only (Phase 1 uses API key / trusted network) |
| Original photos | MinIO `people-photos` | Presigned GET URLs; no public bucket |
| Face crops | MinIO `face-crops` | Presigned GET URLs; no public bucket |
| Embeddings | Qdrant collection vectors | Internal service access only |
| National ID / DOB / full PII | Must not be stored unless explicitly required | N/A |
| Audit log | PostgreSQL `audit_log` | Read-only via `GET /audit`; never stores images/vectors |

## PII rules

- Do not use national ID as a primary key or expose it as an ID.
- Do not store raw national ID unless a future governance decision explicitly requires it.
- Do not store date of birth unless required by API contract.
- Do not store embeddings in PostgreSQL.
- Do not store image bytes, base64, or raw pixels in PostgreSQL or audit log.
- Do not put names, national IDs, or full person metadata in Qdrant payload.

## How MergenVision will adapt this

- **Input validation**:
  - Strict MIME-type allowlist: `image/jpeg`, `image/png`.
  - Max file size from config.
  - Image dimension validation after decode.
  - Object key sanitization; no user-controlled path segments.
- **Authentication** (Phase 1 minimal):
  - Use a single API key loaded from env.
  - Dependency `require_api_key` applied to all mutating and sensitive routes.
  - `GET /health` and `GET /ready` are public for orchestrator health checks.
- **Authorization** (Phase 1 minimal):
  - No per-user RBAC or multitenancy.
  - Future RBAC/KMS is explicitly deferred.
- **MinIO access**:
  - Use presigned URLs with short expiry (default 5 minutes).
  - No public read bucket policy.
  - `GET /media/{bucket}/{objectKey}` validates bucket allowlist and key pattern.
- **Audit logging**:
  - Every `POST /people`, `PATCH /people/{personId}`, `DELETE /people/{personId}`, `POST /people/{personId}/photos`, `DELETE /people/{personId}/photos/{photoId}`, `POST /identify` creates an `audit_log` row.
  - Audit payload includes `action`, `entityType`, `entityId`, `requestId`, `actor`, `timestamp`, `outcome`.
  - No raw images, vectors, national IDs, or full person details.
- **Error responses**:
  - Do not leak stack traces, SQL, internal paths, or provider details to clients.
  - Log full exceptions server-side with structured logging.
- **Secrets management**:
  - All secrets in env vars or Docker secrets; never commit secrets.
  - `app/core/config.py` uses Pydantic `SecretStr` for keys.
- **Image retention**:
  - Query images deleted after request unless retention policy is enabled.
  - Deleted person/photo rows are soft-deleted; object cleanup happens in a later admin/background phase.

## Threats accepted for Phase 1

- No end-to-end encryption at rest beyond MinIO/PostgreSQL defaults.
- No network-level mTLS inside the Docker network.
- No advanced anonymization or differential privacy.
- These are recorded as future hardening items.

## Files to be created in later phases

- `backend/app/core/security.py`
- `backend/app/api/dependencies.py` (auth dependency)
- `backend/app/core/errors.py` ( sanitized error responses )
- `backend/app/application/audit_service.py`

## Verification plan

- Audit all request/response schemas for PII.
- Confirm Qdrant payload excludes names, national IDs, full metadata.
- Confirm PostgreSQL does not store embeddings or image bytes.
- Confirm audit log entries contain no base64 images or vectors.
