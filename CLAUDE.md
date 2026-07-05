# MergenVision — Claude Agent Instructions

> Project: MergenVision  
> Path: `/home/user/MergenVision`  
> Goal: Build a single shared identity platform for photo-based person recognition (Phase 1) and future video-based recognition (Phase 2).

**Before coding, read `AGENTS.md` and the relevant source-of-truth documents. Do not code from memory.**

This file repeats the rules in `AGENTS.md` and adds Claude-agent-specific instructions.

## Claude-Specific Instruction

Before every coding session:

1. Read `AGENTS.md` again.
2. Read the relevant architecture/governance docs for the current task.
3. Read the relevant requirements and reference policy.
4. Produce the required `REFERENCE_CHECK` before writing code.
5. Do not rely on training-data memory for MergenVision architecture, routes, tables, model behavior, or Docker/GPU setup.

## Universal Rule: Reference-First / MCP-First / No-Arbitrary-Implementation

1. Do not code from memory.
2. Do not invent architecture.
3. Do not skip MCP or tool usage.
4. Do not ignore open-source references or official docs.
5. Do not silently change architecture decisions.
6. Do not implement arbitrary solutions without first checking how upstream/open-source projects do it.

## Agent Execution Discipline

> These rules are binding for every autonomous agent working on MergenVision.

### Reference-First / No Arbitrary Implementation

- Read `opensourceReferences/references.md` BEFORE writing any feature.
- Identify relevant upstream repositories from `references.md`.
- For each non-trivial task produce a `REFERENCE_CHECK` block containing: task, references checked, implementation details found, patterns to follow/reject, mapping to MergenVision, files to implement, tests to write.
- If a reference is unclear or missing, STOP and ask.

### Mandatory MCP / Tool Usage

Always prefer these tools over memory/guessing:

1. `codebase-memory-mcp` — `search_graph`, `trace_path`, `get_code_snippet`, `query_graph` for structural discovery.
2. `context7` — `resolve-library-id` → `query-docs` for FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Qdrant, MinIO, TensorRT, torch, torchvision, Docker, Nginx, React/Vite, Mermaid.
3. `deepwiki` — for GitHub repositories listed in `references.md` (insightface, ultralytics, supervision, segment-anything, etc.). Ask concrete implementation questions.
4. `exa` / `webfetch` — primary official docs not covered above.
5. `postman` — required once API runtime exists and endpoint verification is in scope.
6. `playwright` — required only when frontend/UI runtime exists and behavior is in scope.
7. `bash`, `read`, `glob`, `grep`, `edit`, `write` — inspect, run tests, lint, type checks.

### Mandatory Skills

Invoke the relevant skill BEFORE taking action whenever it may apply (even 1% chance):

- `brainstorming` — design/creative decisions
- `writing-plans` — any multi-step task
- `executing-plans` or `subagent-driven-development` — implementing approved plans
- `test-driven-development` — every feature/bugfix
- `systematic-debugging` — any failure
- `verification-before-completion` — before claiming done
- `codebase-memory` — structural code queries
- `context7-mcp` — library/framework questions

### Planning Before Code

- Write or update a design spec in `docs/superpowers/specs/`.
- Write or update an implementation plan in `docs/superpowers/plans/`.
- Only begin implementation after the plan is approved.
- No placeholder text (“TODO”, “TBD”, “later”) in specs or plans.

### Verification Before Claiming Completion

1. Identify the verification command.
2. Run it fresh.
3. Read full output and exit code.
4. Confirm the claim is supported.
5. Only then report completion.

## Before Coding: Mandatory REFERENCE_CHECK

Every implementation task must start with a written `REFERENCE_CHECK` containing all fields below. Do not write code before it is written.

```text
REFERENCE_CHECK

Task:
Phase:
Allowed scope:
Files allowed to change:
Files forbidden to change:
Local docs checked:
Architecture docs checked:
Requirements checked:
Official docs checked via context7:
Open-source references checked via exa/web:
Existing local code inspected:
Old lessons checked:
Patterns to follow:
Patterns rejected:
Architecture decisions that apply:
Docker/GPU strategy that applies:
Data ownership rules that apply:
Security/PII rules that apply:
Tests/verification planned:
Unverified assumptions:
Approval gates:
Out-of-scope requests detected:
```

## Source-of-Truth Priority

Read the relevant subset before implementing:

1. Requirements:
   - `requirements/phase1recognitionrequirements.md`
   - `requirements/phase2videorequirements.md`
2. Reference policy:
   - `opensourceReferences/references.md`
3. Governance / Agent discipline:
   - `AGENTS.md`
   - `CLAUDE.md`
4. Architecture docs:
   - `docs/architecture/API_CONTRACT.md`
   - `docs/architecture/DATA_MODEL.md`
   - `docs/architecture/ARCHITECTURE_DECISION_RECORDS.md`
   - `docs/architecture/DIAGRAM_INDEX.md`
5. Model research:
   - `artifacts/model_benchmarks/MODEL_MANIFEST.json`
6. Old/cautionary context (lessons learned only):
   - `olderDiagramsProvedWrog/`
   - `/home/user/Demo/Demo12_VGGFace2Lab/docs/`
   - `/home/user/Demo/VideoFaceGpuLab/docs/`

If a source file is missing, report it, search safely, and do not invent its contents.

## Mandatory MCP / Tool Usage

Always inspect with:

- `codebase-memory-mcp` — required for repo structure, architecture docs, model research, old reports, avoiding duplicate/conflicting docs.
- `context7` — required before architecture/code decisions involving FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Qdrant, MinIO, ONNX Runtime, Docker Compose, NVIDIA GPU runtime, Nginx, React/Vite, testing frameworks, Mermaid.

Use when needed:

- `exa` / web — official upstream docs not in Context7, GitHub/open-source implementations, model repos, model cards, reference implementations. Prefer primary sources; random blogs are secondary only.
- `postman` — required only when API runtime exists and endpoint verification is in scope; otherwise explicitly mark skipped.
- `playwright` — required only when frontend/UI runtime exists and UI behavior is in scope; otherwise explicitly mark skipped.
- filesystem / shell tools — required for file checks, git status, grep, tests, lint/typecheck. Use `bash`, `read`, `glob`, `grep` as appropriate.

Forbidden:

- `ruflo`
- `21st`
- `https://21st.dev/api/mcp`

## Mandatory Skills

Use and report in every phase:

- brainstorming
- writing-plans
- executing-plans
- systematic-debugging
- verification-before-completion
- codebase-memory
- context7-mcp
- self-review / code-review

If a skill is not applicable, mark it skipped with reason. Do not omit skill reporting.

## Phase Scope Lock

### Phase 1 Allowed Runtime Routes Only

```text
GET /health
GET /ready
POST /people
GET /people
GET /people/{personId}
PATCH /people/{personId}
DELETE /people/{personId}
POST /people/{personId}/photos
GET /people/{personId}/photos
DELETE /people/{personId}/photos/{photoId}
POST /identify
GET /identification-requests
GET /identification-requests/{requestId}
GET /audit
GET /stats
GET /media/{bucket}/{objectKey}
```

### Forbidden Phase 1 Runtime Routes

```text
/videos/*
/imports/*
/faces/*
/oracle/*
/objects/*
/streams/*
any 501 placeholder route for future APIs
any empty router for future APIs
any OpenAPI exposure for future endpoints
```

### Phase 1 Allowed Tables Only

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

### Forbidden Phase 1 Tables

```text
video_job
video_track
face_video_appearance
import_job
import_job_item
anonymous_face
object_detection_job
```

Future boundaries remain future: Oracle import, video/Phase 2, object detection, 10M production sharding, RBAC/KMS/multitenancy, anonymous_face table.

## No Arbitrary Implementation

Do not:

- invent endpoints not in `API_CONTRACT.md`
- invent tables not in `DATA_MODEL.md`
- invent Docker services not in `RUNTIME_TOPOLOGY.md`
- invent model behavior not verified in Phase 0B
- invent Qdrant collection dimensions
- invent MinIO buckets without matching docs
- invent Oracle integration, video pipeline, or anonymous face identity in Phase 1
- write placeholder future routes, fake runtime `FacePipeline`, or empty routers
- write code that contradicts ADRs
- silently install packages, download models/datasets, commit/push

If a new decision is required: stop, document an ADR, ask for approval if scope changes.

## Docker / GPU Strategy Lock

- Dev/simple mode: client → single `api` → PostgreSQL/Qdrant/MinIO.
- GPU demo mode: client → `api-lb` / nginx → `api-gpu-0`, `api-gpu-1`, `api-gpu-2` → shared PostgreSQL/Qdrant/MinIO.
- `api-gpu-*` run the same backend image and same code.
- Each `api-gpu-*` is pinned to one physical GPU in demo mode and usually sees it as `cuda:0`.
- GPU UUID / device pinning is allowed only in Docker Compose or orchestrator config.
- Python code must not hardcode GPU UUID or assume physical GPU index.
- PostgreSQL/Qdrant/MinIO are shared; replicas must be stateless.
- No permanent separate Phase 1/Phase 2 stacks.
- Phase 2 video workers must be separate `worker-gpu` services that reuse the shared identity platform.

See `docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md` for the full lock.

## Data Ownership Rule

- PostgreSQL owns: person business data, photo/sample metadata, request/history/results, audit log, future video metadata.
- Qdrant owns: vector embeddings, reference-only payload, `isActive`, model/dimension/version-specific collections.
- MinIO owns: original images, face crops, query images if retained, future videos/artifacts.

Never store in Qdrant: raw national ID, full person details, sensitive metadata, image bytes.
Never store in audit: raw national ID, image bytes/base64, embeddings, full sensitive person details.
Never store in PostgreSQL: raw embedding vectors, image bytes.

## Model Adapter Boundary Rule

Boundaries:

```text
ImageValidator
DetectorAdapter
AlignerPreprocessor
RecognizerAdapter
FacePipeline
EnrollmentPipeline
OnlineIdentifyPipeline
FutureBatchEnrollmentPipeline
FutureVideoRecognitionPipeline
```

Rules:

- Detector and recognizer are separate adapters.
- Alignment/preprocessing is its own boundary.
- `FacePipeline` orchestrates ML only; business services decide enrollment/search/audit.
- Model config comes from env/config/model registry.
- Store `modelName`, `modelVersion`, `embeddingDimension` in `face_sample`.
- Store `qdrantPointId` and `collectionName` or equivalent reference.
- Qdrant collection dimension must match recognizer output; do not mix ArcFace 512-D and SFace 128-D in same collection.
- Batch support is a performance feature, not a business-domain dependency.
- Adapter + collection strategy must allow model replacement without changing person identity tables.

Forbidden:

- fake production `FacePipeline`
- random embeddings in runtime code
- hardcoded model path in business logic
- business schema depending on SCRFD/ArcFace specifically
- Qdrant collection hardcoded without model/version logic

## UUIDv7 Rule

Use UUIDv7 for new IDs:

```text
personId
photoId
sampleId
requestId
queryFaceId
resultId
auditId
jobId
processId
trackId
artifactId
```

Do not use UUIDv4 without a strong documented reason. Do not use national ID as primary key or expose it as ID.

## Verification-Before-Completion Rule

Before claiming completion:

1. Identify the verification command.
2. Run it fresh.
3. Read full output and exit code.
4. Verify the claim is supported.
5. Only then claim status.

Do not use "should", "probably", "seems to", or express satisfaction before verification.

## Final Report Format

Every phase must end with a Turkish report containing:

```text
MERGENVISION_TASK_STATUS: pass/partial/fail

What changed:
- ...

Why:
- ...

MCP/tools used:
- codebase-memory-mcp: ...
- context7: ...
- exa/web: ...
- postman: ...
- playwright: ...
- bash/filesystem: ...

Skills used:
- ...

Verification:
- tests: ...
- lint/typecheck: ...
- grep checks: ...
- git status: ...
- diff stat: ...

Unverified assumptions:
- ...

Next recommended step:
- ...
```

## Files You May Touch / Must Not Touch

Allowed in governance/documentation phases:

- `AGENTS.md`, `CLAUDE.md`
- `docs/architecture/*` governance and architecture docs

Allowed in implementation phases (when explicitly approved):

- specified backend/app files
- specified frontend files
- specified tests
- specified config

Always forbidden unless scope explicitly says otherwise:

- application code in governance mode
- backend/frontend folders in governance mode
- migrations in governance mode
- Docker Compose files in governance mode
- placeholder routes (`/videos/*`, `/imports/*`, `/faces/*`, etc.) in Phase 1
- model inference code unless Phase 0B/1 model verification
- benchmark/LFW unless Phase 0B/1 benchmark
- model/dataset download or package install
- `git add`, `git commit`, `git push`

## Questions / Disambiguation

If scope is ambiguous, stop and ask. Do not guess. Do not implement a "reasonable" superset.
