# Reference-First Checklist

> Use this checklist before writing any MergenVision implementation code.

## Pre-Coding Gate

Do not start coding until every item below is checked or explicitly skipped with reason.

- [ ] I know the current phase (Phase 0B, Phase 1 planning, Phase 1 skeleton, Phase 1 slice, Phase 2, etc.).
- [ ] I know which files are allowed to change for this task.
- [ ] I know which files are forbidden for this task.
- [ ] I have read `AGENTS.md` and `CLAUDE.md`.
- [ ] I have read this `REFERENCE_FIRST_CHECKLIST.md`.
- [ ] I have read `docs/architecture/IMPLEMENTATION_GOVERNANCE.md`.
- [ ] I have read the relevant requirements (`phase1recognitionrequirements.md` and/or `phase2videorequirements.md`).
- [ ] I have read `opensourceReferences/references.md`.
- [ ] I have read the relevant architecture docs.
- [ ] I have produced a complete `REFERENCE_CHECK`.
- [ ] The `REFERENCE_CHECK` includes `Out-of-scope requests detected:`.
- [ ] I have run `git status` and know the current workspace state.

## REFERENCE_CHECK Template

Copy this template into your task notes and fill every field.

```text
REFERENCE_CHECK

Task:
- <clear one-line description>

Phase:
- <Phase 0B / Phase 1 planning / Phase 1 slice name / Phase 2 future>

Allowed scope:
- <what this task is allowed to do>

Files allowed to change:
- <exact file paths>

Files forbidden to change:
- <exact file paths or patterns>

Local docs checked:
- <list files read>

Architecture docs checked:
- <list architecture files read>

Requirements checked:
- <list requirement files read>

Official docs checked via context7:
- <list library IDs and topics, or "not applicable">

Open-source references checked via exa/web:
- <list URLs/repos and what was learned, or "not applicable">

Existing local code inspected:
- <list files/modules reviewed>

Old lessons checked:
- <list old docs reviewed, or "not applicable">

Patterns to follow:
- <patterns approved for this task>

Patterns rejected:
- <patterns explicitly rejected>

Architecture decisions that apply:
- <ADR numbers and why>

Docker/GPU strategy that applies:
- <which topology or rule>

Data ownership rules that apply:
- <what goes into PostgreSQL/Qdrant/MinIO>

Security/PII rules that apply:
- <what must not be stored where>

Tests/verification planned:
- <test files and commands>

Unverified assumptions:
- <assumptions that cannot be proven yet>

Approval gates:
- <any user approvals needed>

Out-of-scope requests detected:
- <any creeping requests, or "none">
```

## Local Docs Checklist

Before coding, read these when relevant:

- [ ] `requirements/phase1recognitionrequirements.md` — Phase 1 photo-based person recognition.
- [ ] `requirements/phase2videorequirements.md` — Phase 2 video; treat as future boundary unless explicitly in Phase 2.
- [ ] `opensourceReferences/references.md` — reference-first policy and external links.
- [ ] `AGENTS.md` — project agent rules.
- [ ] `CLAUDE.md` — Claude-specific agent rules.
- [ ] `docs/architecture/IMPLEMENTATION_GOVERNANCE.md` — governance gates.
- [ ] `docs/architecture/MCP_TOOL_USAGE_POLICY.md` — tool usage policy.
- [ ] `docs/architecture/PHASE_IMPLEMENTATION_GATES.md` — phase gates.
- [ ] `docs/architecture/NO_SCOPE_CREEP_RULES.md` — forbidden routes/tables.
- [ ] `docs/architecture/SELF_REVIEW_AND_VERIFICATION_POLICY.md` — verification rules.
- [ ] `docs/architecture/PHASE_0_ARCHITECTURE_PLAN.md` — master plan.
- [ ] `docs/architecture/API_CONTRACT.md` — allowed endpoints and sequences.
- [ ] `docs/architecture/DATA_MODEL.md` — allowed tables and ERD.
- [ ] `docs/architecture/RUNTIME_TOPOLOGY.md` — Docker/GPU topologies.
- [ ] `docs/architecture/MODEL_ADAPTER_BOUNDARY.md` — ML pipeline boundaries.
- [ ] `docs/architecture/PHASE1_PHASE2_SHARED_DATA_PLATFORM.md` — shared data platform.
- [ ] `docs/architecture/SENSITIVE_DATA_RULES.md` — PII and data access.
- [ ] `docs/architecture/FUTURE_BOUNDARIES.md` — future scope.
- [ ] `docs/architecture/ARCHITECTURE_DECISION_RECORDS.md` — ADRs.
- [ ] `docs/architecture/DIAGRAM_INDEX.md` — diagram inventory.
- [ ] `docs/architecture/requirementsmetrix.md` — requirement coverage.
- [ ] `docs/model_research/PHASE_MINUS_1_MODEL_SELECTION_REPORT.md`.
- [ ] `docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md`.
- [ ] `artifacts/model_benchmarks/MODEL_MANIFEST.json`.

## Official Docs Checklist (context7)

Use `context7` before architecture/code decisions involving these topics. Check each that applies:

- [ ] FastAPI — routing, dependencies, APIRouter, bigger applications.
- [ ] Pydantic — models, validation, serialization.
- [ ] SQLAlchemy — 2.0 ORM, models, relationships, transactions.
- [ ] Alembic — migration organization, revision generation, branching.
- [ ] PostgreSQL — SQL features, job queues (`SKIP LOCKED`), types.
- [ ] Qdrant — collections, vector dimensions, payload, upsert, search.
- [ ] MinIO — bucket/object operations, presigned URLs.
- [ ] ONNX Runtime — execution providers, sessions, IOBinding, batch.
- [ ] Docker Compose — services, networks, GPU device reservations.
- [ ] NVIDIA GPU runtime / Docker GPU mapping — device visibility.
- [ ] Nginx — upstream/load balancing/reverse proxy.
- [ ] React / Vite — only if UI work is in scope.
- [ ] Testing framework — only if tests are in scope.
- [ ] Mermaid — only if diagrams are being created or updated.

## Open-Source / Upstream Comparison Checklist

For non-trivial tasks, complete these checks:

- [ ] I have identified at least one upstream or open-source reference for the task.
- [ ] I have read the relevant part of the reference, not just a snippet.
- [ ] I have noted the patterns the reference uses.
- [ ] I have noted why those patterns do or do not fit MergenVision.
- [ ] If no good reference exists, I have recorded that in `REFERENCE_CHECK`.

Common reference topics:

- FastAPI larger application structure.
- SQLAlchemy 2.0 + Alembic project layout.
- Qdrant payload design and search patterns.
- MinIO presigned-URL patterns.
- ONNX Runtime provider/device handling and IOBinding.
- Docker Compose multi-service GPU setup.
- Nginx upstream load balancing.
- SCRFD/ArcFace adapter examples (prefer official/model-card sources; avoid blind copy-paste).

## Old Lessons Checklist

Use old reports only as cautionary context. Do not treat them as source of truth.

- [ ] `olderDiagramsProvedWrog/` — reviewed for known mistakes.
- [ ] `/home/user/Demo/VideoFaceGpuLab/docs/` — reviewed if video/GPU worker patterns are relevant.
- [ ] `/home/user/Demo/Demo12_VGGFace2Lab/docs/` — reviewed if batch ONNX/multi-GPU/data deletion patterns are relevant.

For each old doc used, write one sentence about what lesson was learned, not what code was copied.

## Decision Log Template

If a reference check leads to a new local decision, record it:

```text
DECISION

Date: <YYYY-MM-DD>
Task: <name>
Decision: <what was decided>
Rationale: <why>
Risk: <what could go wrong>
ADR needed: yes / no
Approved by: <user> / self (within allowed scope)
```

## Missing-Reference Escalation

If a required reference is missing or unclear:

1. Do not invent its contents.
2. Record the missing reference in `REFERENCE_CHECK` under `Unverified assumptions:`.
3. If the missing reference blocks implementation, stop and ask.
4. If the task can proceed safely with a documented risk, say so explicitly.
