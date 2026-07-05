# MergenVision Implementation Governance

> **Status:** Accepted  
> **Scope:** All future MergenVision phases (Phase 0B, Phase 1, Phase 2, and beyond).  
> **Applies to:** Every agent, assistant, or human contributor before writing code.

## Purpose

This document locks the rules that every future implementation phase must follow. It exists so that future agents cannot silently change architecture, skip references, or add out-of-scope features.

## Golden Rules

1. **Reference-first.** Check local docs, official docs, and open-source references before coding.
2. **MCP/tool-first.** Use `codebase-memory-mcp` and `context7` as the default discovery path; fall back to `exa`/web when needed.
3. **No arbitrary implementation.** If a design decision is not already written in the architecture docs, stop and write an ADR or ask for approval.
4. **Phase scope lock.** Phase 1 contains only the agreed routes and tables. Future routes/tables stay future.
5. **Verify before claiming completion.** Every claim must be backed by fresh command output.

## Phase Gates

Every future implementation phase must go through these gates in order:

### 1. Scope Confirmation

Answer explicitly:

- What phase is this?
- What files are allowed to change?
- What files are forbidden?
- Which docs are the source of truth?

If any answer is unclear, stop and ask.

### 2. REFERENCE_CHECK

Complete the `REFERENCE_CHECK` template (see `REFERENCE_FIRST_CHECKLIST.md`). Do not write code before it is written.

### 3. Implementation Plan

The plan must contain:

- Exact file list (create/modify/delete).
- Exact commands (including tests and lint/typecheck).
- Rollback plan.
- Risks.
- Unverified assumptions.
- Approval gates.

### 4. Approval / Gate Check

- If the user explicitly asked for implementation within a clear scope, proceed.
- If scope is ambiguous, ask before coding.
- If scope creep is detected, stop.

### 5. Implementation

- Smallest coherent slice.
- No future routes/tables.
- No fake production pipeline.
- No silent package/model installs.
- No silent commits.

### 6. Verification

- Run the identified command.
- Read output and exit code.
- Run grep checks (routes, tables, GPU hardcoding, fake pipeline markers).
- Inspect `git status` and `git diff`.
- Verify no forbidden files/routes/tables were added.

### 7. Final Turkish Report

Use the format in `SELF_REVIEW_AND_VERIFICATION_POLICY.md`.

## Source-of-Truth Hierarchy

Highest priority first:

1. User explicit instructions (`AGENTS.md`, `CLAUDE.md`, direct requests).
2. Governance docs (this file and siblings).
3. Requirements (`requirements/phase1recognitionrequirements.md`, `requirements/phase2videorequirements.md`).
4. Reference policy (`opensourceReferences/references.md`).
5. Architecture docs (`PHASE_0_ARCHITECTURE_PLAN.md`, `API_CONTRACT.md`, `DATA_MODEL.md`, `RUNTIME_TOPOLOGY.md`, etc.).
6. Model research (`PHASE_MINUS_1_MODEL_SELECTION_REPORT.md`, `PHASE_0A_MODEL_ACCESS_REPORT.md`, `MODEL_MANIFEST.json`).
7. Old reports (`olderDiagramsProvedWrog/`, `VideoFaceGpuLab`, `Demo12_VGGFace2Lab`) — lessons learned only.
8. Official docs (`context7`) and open-source references (`exa`/web).

Lower-priority sources must not contradict higher-priority sources without an explicit ADR and approval.

## Reference-First Rule

Before coding any non-trivial task, produce:

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

Use `REFERENCE_FIRST_CHECKLIST.md` to verify every field is filled.

## MCP / Tool Usage Policy Summary

- `codebase-memory-mcp` — required always for structure, code discovery, and impact analysis.
- `context7` — required whenever implementation touches FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Qdrant, MinIO, ONNX Runtime, Docker Compose, NVIDIA GPU runtime, Nginx, React/Vite, testing frameworks, or Mermaid.
- `exa`/web — required when context7 is insufficient or open-source comparison is needed.
- `postman` — required only when an API runtime exists and endpoint verification is in scope.
- `playwright` — required only when a frontend/UI runtime exists and UI behavior is in scope.
- `bash` / filesystem tools — required for git status, grep checks, tests, lint/typecheck.
- `ruflo`, `21st`, `https://21st.dev/api/mcp` — forbidden.

Document every tool used in the final report with purpose and result.

## Open-Source / Upstream Comparison Rule

For every non-trivial implementation task, check how others do it before writing code.

Examples:

- **FastAPI app structure** — use `context7` FastAPI bigger-applications / APIRouter docs.
- **SQLAlchemy/Alembic** — use `context7` SQLAlchemy 2.0 and Alembic docs.
- **Qdrant** — use `context7` Qdrant collection/search/upsert/payload docs.
- **MinIO** — use `context7` MinIO bucket/object/presigned URL docs.
- **ONNX Runtime** — use `context7` ONNX Runtime provider/session/IOBinding docs.
- **Docker/GPU** — use `context7` Docker Compose GPU device reservation docs.
- **Nginx** — use `context7`/official upstream load-balancing docs before implementing `api-lb`.
- **React/Vite** — use official docs; UI is demo/admin only unless product owner confirms otherwise.
- **Model adapters** — use `context7` ONNX Runtime docs and model source/model card; do not hardcode SCRFD/ArcFace.

If no good upstream reference exists, state that clearly, choose the simplest design, document it as a local architecture decision, and add a risk/open question.

## No-Arbitrary-Implementation Rule

Do not:

- invent endpoints not in `API_CONTRACT.md`
- invent tables not in `DATA_MODEL.md`
- invent Docker services not in `RUNTIME_TOPOLOGY.md`
- invent model behavior not verified in Phase 0B
- invent Qdrant collection dimensions
- invent MinIO buckets without matching docs
- invent Oracle integration
- invent video pipeline in Phase 1
- invent anonymous face identity in Phase 1
- write placeholder future routes
- write fake runtime `FacePipeline`
- write code that contradicts ADRs
- silently change architecture decisions
- silently bypass missing requirements
- silently install packages
- silently download models/datasets
- silently commit/push
- use old project code as truth without verifying

If implementation requires a new decision:

1. Stop.
2. Document the decision in `ARCHITECTURE_DECISION_RECORDS.md` or as a proposal.
3. Ask for approval if scope changes.

## Scope Creep Stop Conditions

Stop immediately when any of the following appear:

- A request to add `/videos/*`, `/imports/*`, `/faces/*`, `/oracle/*`, `/objects/*`, or `/streams/*` to Phase 1.
- A request to create `video_job`, `video_track`, `face_video_appearance`, `import_job`, `import_job_item`, `anonymous_face`, `face_identity`, or `object_detection_job` in Phase 1.
- A request to implement Oracle import, TensorRT, production RBAC/KMS, 10M sharding, or object detection in Phase 1.
- A request to add 501 placeholder routes or empty routers for future APIs.
- A request to implement a fake runtime pipeline that returns random embeddings.
- A request to silently change a previous ADR.

When scope creep is detected, do not implement it. Report it in the `Out-of-scope requests detected:` field of `REFERENCE_CHECK` and in the final report.

## User Approval Conditions

Certain changes require explicit user approval before proceeding:

- Adding an endpoint not in `API_CONTRACT.md`.
- Adding a table not in `DATA_MODEL.md`.
- Changing an accepted ADR.
- Changing the Docker/GPU strategy.
- Adding a new model or changing the primary model pair (SCRFD+ArcFace).
- Moving a future boundary item into Phase 1.
- Changing data-ownership rules (what goes into PostgreSQL / Qdrant / MinIO).
- Introducing a new third-party package or model download.
- Committing or pushing code.

## Supporting Rules

- **Data ownership** — PostgreSQL owns business metadata and audit; Qdrant owns vectors and reference payload only; MinIO owns binary objects. See `SENSITIVE_DATA_RULES.md`.
- **Model adapter boundary** — preserve `ImageValidator`, `DetectorAdapter`, `AlignerPreprocessor`, `RecognizerAdapter`, `FacePipeline` boundaries. See `MODEL_ADAPTER_BOUNDARY.md`.
- **Docker/GPU strategy** — dev/simple and GPU demo topologies are locked; see `DOCKER_GPU_STRATEGY_LOCK.md`.
- **UUIDv7** — new IDs use UUIDv7. See `AGENTS.md`.
- **Verification** — evidence before claims. See `SELF_REVIEW_AND_VERIFICATION_POLICY.md`.
