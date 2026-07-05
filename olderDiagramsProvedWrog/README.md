# `person-face-identification-demo` Architecture Diagrams

This folder contains the architecture/design diagrams for the `person-face-identification-demo` project.

No application code lives here — only design documentation and Mermaid diagrams.

## Runtime Notes

- **Production-style GPU path**: `frontend` → `api-lb` (nginx, `localhost:8080`) → `api-gpu-0` / `api-gpu-1` / `api-gpu-2`. Each GPU worker is pinned to a dedicated physical GPU.
- **Single-instance dev/fallback path**: `frontend` → `api` (FastAPI, `localhost:8000`). This container is useful for development, testing, or fallback and does not require a multi-GPU host.
- **Oracle import**: Mentioned in some diagrams as a future external import source; there is no live Oracle connection, importer service, or async job queue in the current codebase.

## Files

| # | File | Purpose | Review Order |
|---|------|---------|--------------|
| 1 | [`01_system_purpose.md`](./01_system_purpose.md) | What the system does, what enrollment/identification mean, what is stored where, and what is out of scope. | **Start here** |
| 2 | [`02_high_level_architecture.md`](./02_high_level_architecture.md) | Logical high-level view: User, React + Vite UI, Docker runtime (`api`, `api-lb`, `api-gpu-*`), FastAPI app layers, PostgreSQL, Qdrant, MinIO, and future Oracle source. | 2 |
| 3 | [`03_docker_compose_architecture.md`](./03_docker_compose_architecture.md) | Docker Compose runtime and 3-GPU deployment view with ports, GPU pinning, and service names. | 3 |
| 4 | [`04_layered_backend_architecture.md`](./04_layered_backend_architecture.md) | Clean layered backend structure, dependency rules, and runtime note that the same code runs in `api` and `api-gpu-*` containers. | 4 |
| 6 | [`06_database_erd.md`](./06_database_erd.md) | PostgreSQL entity-relationship diagram. | 6 |
| 7 | [`07_enrollment_sequence.md`](./07_enrollment_sequence.md) | Enrollment flow sequence diagram. | 7 |
| 8 | [`08_identification_sequence.md`](./08_identification_sequence.md) | Photo identification flow sequence diagram. | 8 |
| 9 | [`09_ui_wireflow.md`](./09_ui_wireflow.md) | UI page map and Identify Photo page structure. | 9 |
| 10 | [`10_api_map.md`](./10_api_map.md) | Endpoint list with purpose, inputs, outputs, and errors. | 10 |
| 11 | [`11_demo_vs_future_scope.md`](./11_demo_vs_future_scope.md) | Demo scope vs. future scope split. | 11 |
| 12 | [`12_risks_and_open_questions.md`](./12_risks_and_open_questions.md) | Risks and open human decisions before coding. | 12 |

## Recommended Review Flow

1. Read `01_system_purpose.md` to agree on terminology.
2. Review `02_high_level_architecture.md`, `03_docker_compose_architecture.md`, and `04_layered_backend_architecture.md` to validate components, runtime layout, and dependency direction.
3. Review `05_data_ownership.md` and `06_database_erd.md` to validate data ownership and schema.
4. Review `07_enrollment_sequence.md` and `08_identification_sequence.md` to validate flows.
5. Review `09_ui_wireflow.md` and `10_api_map.md` for UI/API alignment.
6. Review `11_demo_vs_future_scope.md` and `12_risks_and_open_questions.md` to lock scope before implementation.
