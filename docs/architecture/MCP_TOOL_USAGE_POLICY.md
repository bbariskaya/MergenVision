# MCP / Tool Usage Policy

> **Status:** Accepted  
> **Scope:** All future MergenVision phases.

This document locks which tools must be used, when they may be skipped, and which tools are forbidden.

## Required Tools

### 1. codebase-memory-mcp — Required Always

Use for:

- Inspecting current MergenVision repo structure.
- Finding existing architecture docs.
- Finding model research docs.
- Finding requirements docs.
- Finding old diagrams and reports.
- Checking whether governance docs already exist.
- Avoiding duplicate or conflicting documents.
- Checking old VGGFace2 / VideoFaceGpuLab lessons when relevant.
- Tracing call paths and impact analysis during implementation.

Skip only if the MCP server is unavailable. If skipped, document the reason and fall back to `read`, `glob`, and `grep`.

### 2. context7 — Required for Implementation-Relevant Topics

Use before architecture/code decisions involving:

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Qdrant
- MinIO
- ONNX Runtime
- Docker Compose
- NVIDIA GPU runtime / Docker GPU mapping
- Nginx
- React / Vite (if UI is touched)
- Testing frameworks (if tests are touched)
- Mermaid (if diagrams are touched)

Procedure:

1. Call `context7_resolve-library-id` with the official library name and task question.
2. Select the best library ID by name match, description, code-snippet coverage, reputation, and benchmark score.
3. Call `context7_query-docs` with the chosen library ID and a specific question.

If context7 returns no useful result, record that fact and use `exa`/web as fallback.

### 3. Filesystem / Shell Tools — Required for Verification

Use for:

- Listing files before changes.
- Checking `git status`, `git diff`, and `git diff --name-only`.
- Verifying created/updated files.
- Running grep checks for forbidden routes/tables/scope creep.
- Running tests, lint, or typecheck when implementation phase allows.

Preferred tools: `bash`, `read`, `glob`, `grep`, `edit`, `write`.

## Conditionally Required Tools

### 4. exa / web — Required When Context7 Is Insufficient

Use for:

- Official upstream docs not in Context7.
- GitHub / open-source implementations.
- Model repos and model cards.
- Reference implementations.
- Current library behavior.

Rules:

- Do not rely on search snippets only; open primary sources where possible.
- Prefer official docs and reputable upstream repos.
- Do not use random blogs as source of truth unless clearly marked as secondary.
- Record exact URLs and what was learned.

### 5. postman — Required When API Exists or Is Being Tested

Use/skip policy:

- If a local Postman collection exists, inspect it.
- If an API runtime exists and endpoint verification is in scope, use it or recommend collection updates.
- If no API runtime exists, explicitly mark skipped with reason.

### 6. playwright — Required When UI Exists or UI Behavior Is Being Tested

Use/skip policy:

- If a frontend exists and UI behavior is in scope, use Playwright or browser automation.
- If no UI runtime exists, explicitly mark skipped with reason.

## Forbidden Tools

These tools are forbidden for MergenVision:

- `ruflo`
- `21st`
- `https://21st.dev/api/mcp`

Never invoke them. If they appear in a tool list, ignore them.

## Tool Accountability Table Template

Use this table or a textual equivalent in every final report:

| Tool | Purpose | Used? | Result / Notes |
|---|---|---|---|
| `codebase-memory-mcp` | repo/doc discovery, impact analysis | yes/no | ... |
| `context7` | official docs for <list topics> | yes/no | ... |
| `exa` / web | open-source/official reference for <topic> | yes/no | ... |
| `postman` | API verification | yes/no | skipped if no runtime |
| `playwright` | UI verification | yes/no | skipped if no runtime |
| `bash` / filesystem | git/grep/test/lint checks | yes/no | ... |
| `ruflo` | forbidden | no | — |
| `21st` | forbidden | no | — |

## Example Accountability Note

```text
MCP/tools used:
- codebase-memory-mcp: repo inspection and architecture doc lookup.
- context7: FastAPI dependency injection, SQLAlchemy 2.0 relationships, Qdrant search.
- exa/web: FastAPI best-practice project structure from official docs.
- postman: skipped; no API runtime exists yet.
- playwright: skipped; no UI runtime exists yet.
- bash/filesystem: git status, grep scope checks, pytest.
- ruflo: forbidden, not used.
- 21st: forbidden, not used.
```

## Compliance

If a tool is required but cannot be used (e.g., server unavailable), record the failure and the fallback. Do not silently drop required tool usage from the report.
