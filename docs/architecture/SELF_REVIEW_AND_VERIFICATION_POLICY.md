# Self-Review and Verification Policy

> **Status:** Accepted  
> **Scope:** All future MergenVision implementation phases.

This document defines the minimum verification that must be performed before claiming any task is complete.

## Core Principle

Evidence before claims. No status report may say "pass", "complete", "done", or "working" unless fresh verification output supports it.

## Verification Gate

Before claiming completion:

1. **Identify** the command that proves the claim.
2. **Run** the full command fresh.
3. **Read** the full output and exit code.
4. **Verify** the output supports the claim.
5. **Report** the actual output or a faithful summary.

Do not use words like "should", "probably", or "seems to".

## Required Verification Commands

Run these in every implementation phase before the final report:

```bash
pwd
git status --short || true
git diff --stat || true
git diff --name-only || true
```

## Route-Scope Safety Grep

```bash
grep -R "videos" -n backend app src . || true
grep -R "imports" -n backend app src . || true
grep -R "faces" -n backend app src . || true
grep -R "oracle" -n backend app src . || true
```

Interpretation:

- These greps are not automatic failures.
- Explain every hit.
- Docs may mention forbidden routes; runtime code must not include them.
- Test stubs that verify rejection of future routes are allowed if clearly named.

## Table-Scope Safety Grep

```bash
grep -R "video_job\|video_track\|face_video_appearance\|import_job\|anonymous_face\|face_identity" -n backend app src alembic . || true
```

Interpretation:

- Forbidden tables must not appear in migrations, models, or runtime code in Phase 1.
- Allowed mentions in architecture docs and governance docs do not count.

## Data / Model Metadata Grep

```bash
grep -R "UUIDv7\|uuid7\|modelName\|modelVersion\|embeddingDimension\|qdrantPointId\|collectionName" -n backend app src docs . || true
```

Interpretation:

- Expect hits for UUIDv7 and model metadata fields in implementation code and architecture docs.
- Ensure these fields are stored where required (e.g., `modelName`/`modelVersion`/`embeddingDimension` on `face_sample`).

## Fake Pipeline Safety Grep

```bash
grep -R "fake\|dummy\|random embedding\|random_embedding\|placeholder" -n backend app src . || true
```

Interpretation:

- Production runtime code must not contain fake embeddings or placeholder inference.
- Test-only stubs clearly named (e.g., `test_onnx_stub.py`) are allowed.

## Docker / GPU Safety Grep

```bash
grep -R "GPU-\|CUDA_VISIBLE_DEVICES\|NVIDIA_VISIBLE_DEVICES" -n backend app src docker-compose* . || true
```

Interpretation:

- GPU UUID strings and device pinning must not appear in application source code.
- They are allowed only in Docker Compose or orchestrator configuration files.

## Test Verification

Run the relevant test command for the phase:

```bash
pytest tests/ -v
# or the specific test file for the slice
```

Read the output. Confirm pass/fail counts.

## Lint / Typecheck Verification

Run lint and typecheck commands if they are defined:

```bash
ruff check .
mypy app/
# or project-specific equivalents: npm run lint, npm run typecheck, etc.
```

If the project does not yet have lint/typecheck configured, record that as unverified and recommend adding them.

## Git Diff Review

Before the final report:

1. Run `git diff --stat`.
2. Run `git diff --name-only`.
3. Scan the diff for unintended files or forbidden content.
4. Confirm only allowed files were changed.
5. Do not stage (`git add`) or commit unless explicitly asked.

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
- brainstorming: ...
- writing-plans: ...
- executing-plans: ...
- systematic-debugging: ...
- verification-before-completion: ...
- codebase-memory: ...
- context7-mcp: ...
- self-review/code-review: ...

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

## Failure Reporting

If verification fails:

1. Report the exact failure and command output.
2. Do not claim the task passed.
3. Use `MERGENVISION_TASK_STATUS: partial` or `fail`.
4. Describe what remains broken.
5. Recommend the next action.

Do not silently leave failed checks out of the final report.
