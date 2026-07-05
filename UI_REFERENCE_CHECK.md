# UI_REFERENCE_CHECK — MergenVision Phase 1 Admin/Operations Panel

```text
REFERENCES

Task:
  Design and plan the Phase 1 MergenVision admin/operations UI (React + Vite + Tailwind v3 +
  shadcn/ui). Output: UI_REFERENCE_CHECK.md, docs/superpowers/specs/2026-07-04-phase1-ui-design.md,
  docs/superpowers/plans/2026-07-04-phase1-ui-plan.md.

Phase:
  Phase 1

Allowed scope:
  - Frontend pages built only on Phase 1 endpoints/routes and tables.
  - Allowed routes: /health, /ready, /people, /people/{personId}, /people/{personId}/photos,
    /identify, /identification-requests, /identification-requests/{requestId}, /audit, /stats,
    /media/{bucket}/{objectKey}.
  - Allowed tables: person, person_photo, face_identity, face_sample, identification_request,
    identification_query_face, identification_result, audit_log.
  - Display nationalId in masked form only; never show raw nationalId, nationalIdHash, or
    embeddings.

Files allowed to change:
  - docs/superpowers/specs/2026-07-04-phase1-ui-design.md
  - docs/superpowers/plans/2026-07-04-phase1-ui-plan.md
  - UI_REFERENCE_CHECK.md
  - frontend/ (only after design spec approval)

Files forbidden to change:
  - backend/* (Dockerfile, source code, migrations, compose files)
  - docs/architecture/API_CONTRACT.md
  - docs/architecture/DATA_MODEL.md
  - Any file outside frontend/ unless explicitly scoped

Local docs checked:
  - docs/architecture/API_CONTRACT.md
  - docs/architecture/DATA_MODEL.md
  - requirements/phase1recognitionrequirements.md
  - docs/fastestplan.md
  - docs/architecture/PHASE_1_SCOPE_LOCK.md (checked; file not present, scope defined by API_CONTRACT + DATA_MODEL)
  - docs/architecture/NO_SCOPE_CREEP_RULES.md (checked; file not present)
  - AGENTS.md
  - CLAUDE.md
  - frontend/package.json
  - frontend/vite.config.ts
  - frontend/src/main.tsx

Architecture docs checked:
  - docs/architecture/API_CONTRACT.md
  - docs/architecture/DATA_MODEL.md

Requirements checked:
  - requirements/phase1recognitionrequirements.md

Official docs checked via context7:
  - Tailwind CSS v3 installation with Vite/React TS (/websites/v3_tailwindcss)
  - React Router v6 createBrowserRouter + nested layouts (/websites/reactrouter_6_30_3)
  - TanStack Query v5 QueryClient / useQuery / useMutation / invalidation (/tanstack/query)

Open-source references checked via exa/web:
  - INTERPROBE official website (interprobe.com.tr) — brand, slogan, services
  - Face recognition admin dashboard examples (VisionTrack UI Kit, FaceBase, FaceMark)
  - Security operations dashboard patterns

Existing local code inspected:
  - frontend/ is currently React 19 + Tailwind v4. It will be deleted and rebuilt as React 18 +
    Tailwind v3 with shadcn/ui per approved design.

Old lessons checked:
  - olderDiagramsProvedWrog/ reviewed; no active UI decisions depend on these files.

Patterns to follow:
  - shadcn/ui base components installed via CLI with Tailwind v3 theme.
  - React Router v6 `createBrowserRouter` with nested layout routes and `<Outlet>`.
  - TanStack Query v5 for server state; cache invalidation on mutations.
  - Axios instance with `Authorization: Bearer <token>` interceptor; token stored in Zustand +
    localStorage.
  - React Hook Form + Zod for forms, Zod resolver from @hookform/resolvers.
  - Zustand for client-side global UI state (auth token, sidebar collapse, theme preference).
  - Dark mode default; light mode optional via CSS variables/class toggle.
  - All images fetched through `/media/{bucket}/{objectKey}`; no base64/raw bytes stored in state.

Patterns rejected:
  - Tailwind CSS v4 CSS-first config (prompt requires v3).
  - React 19 (prompt requires React 18).
  - Fully custom component library without shadcn/ui.
  - Phase 2/3 route placeholders or empty routers (videos, imports, oracle, faces, objects, streams).
  - Redux for server state (TanStack Query is sufficient).

Architecture decisions that apply:
  - UUIDv7 IDs are strings in the UI.
  - Pagination shape is { items, total, limit, offset }.
  - Masked national ID format follows backend response (e.g., "******8901").
  - Media URLs are relative to VITE_API_BASE_URL.

Docker/GPU strategy that applies:
  - N/A for frontend design phase.

Data ownership rules that apply:
  - Never persist raw nationalId, nationalIdHash, embedding vectors, or image bytes in localStorage,
    Zustand, or code.
  - Qdrant point IDs and sample metadata may be displayed as reference-only identifiers.

Security/PII rules that apply:
  - Masked national ID only.
  - Token stored in localStorage with XSS-aware caution; no logging of token value.
  - No secrets or API keys hardcoded.

Tests/verification planned:
  - npm run typecheck
  - npm run build
  - npm run lint
  - npm run test
  - npx playwright test

Unverified assumptions:
  - shadcn/ui CLI will accept the Tailwind v3 + Vite React TS setup.
  - VITE_API_BASE_URL defaults to http://localhost:8000.
  - Mock token login is acceptable for Phase 1; real auth is future scope.

Approval gates:
  - User approval of this design spec and implementation plan before any frontend code is written.

Out-of-scope requests detected:
  - Video/Phase 2 screens.
  - Oracle import flows.
  - Real RBAC/KMS/multitenancy.
  - Backend/Docker changes (assigned to other team members).
```

## Source-of-Truth Summary

### Brand — INTERPROBE

- Company: INTERPROBE Bilgi Teknolojileri A.Ş.
- Sector: Cyber security, cyber threat intelligence, next-generation defense technologies, big data
  analytics and AI services.
- Slogan / tagline: **Protect Beyond The Endpoint**
- Services: SOC/NOC/CIC, cyber intelligence, advanced R&D, special software solutions.
- Logo: `https://interprobe.com.tr/themes/interprobe/assets/img/logo.png`
- Favicon: `https://interprobe.com.tr/themes/interprobe/assets/img/fav/android-icon-192x192.png`

### Brand Colors Used in UI

- Background: `#191828`
- Surface/card: `#232336`
- Surface elevated: `#2d2d45`
- Border: `#3a3a55`
- Text primary: `#ffffff`
- Text secondary: `#a0a3bd`
- Primary accent: `#007bff`
- Primary accent hover: `#0056b3`
- Success: `#22c55e`
- Warning: `#f59e0b`
- Danger: `#ef4444`
- Info: `#0ea5e9`

### Phase 1 API Surface Relevant to UI

- `GET /health` → liveness `{ status: "ok" }`
- `GET /ready` → readiness `{ status: "ready" }` or 503
- `GET /stats` → `{ personCount, photoCount, faceSampleCount, identificationRequestCount }`
- `POST /people`, `GET /people`, `GET /people/{id}`, `PATCH /people/{id}`, `DELETE /people/{id}`
- `POST /people/{id}/photos`, `GET /people/{id}/photos`, `DELETE /people/{id}/photos/{photoId}`
- `POST /identify?topK&threshold&selectedFaceIndex`
- `GET /identification-requests`, `GET /identification-requests/{requestId}`
- `GET /audit?entityType&entityId&action&limit&offset`
- `GET /media/{bucket}/{objectKey}`

### Data & PII Rules

- `nationalId` is captured only at person creation; UI always receives `nationalIdMasked`.
- No embedding values, raw nationalId, hashes, or image bytes displayed.
- All images loaded through `/media/{bucket}/{objectKey}`.
