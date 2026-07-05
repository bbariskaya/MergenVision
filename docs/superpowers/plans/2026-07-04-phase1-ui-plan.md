# MergenVision Phase 1 — UI Implementation Plan

> Version: 2026-07-04  
> Stack: React 18 + TypeScript + Vite + Tailwind CSS v3 + shadcn/ui + react-router-dom v6 + @tanstack/react-query v5 + axios + zustand + react-hook-form + zod + lucide-react + recharts + playwright

## Global Constraints

- Phase 1 endpoints only (`API_CONTRACT.md`).
- No Phase 2 routes/pages (videos, imports, oracle, faces, objects, streams).
- Dark mode default; light mode optional.
- `nationalId` is masked in the UI at all times.
- No raw embeddings, hashes, or image bytes stored in UI state/localStorage.
- All media fetched through `/media/{bucket}/{objectKey}`.
- TDD for utils/hooks/components; at least smoke UI tests for pages.
- No git add/commit/push unless explicitly requested.

---

## Task 1 — Project Bootstrap

**Goal:** Replace the existing frontend with a fresh Vite + React 18 + TypeScript + Tailwind v3 project and install the required stack.

### Steps

1. Delete the existing `frontend/` contents except keep `.env`/`.env.example` if they are generic (they will be recreated).
2. Initialize the project:
   ```bash
   cd /home/user/MergenVision
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   ```
3. Install Tailwind CSS v3 + PostCSS + autoprefixer:
   ```bash
   npm install -D tailwindcss@3 postcss autoprefixer
   npx tailwindcss init -p
   ```
4. Install application dependencies:
   ```bash
   npm install react-router-dom @tanstack/react-query @tanstack/react-query-devtools axios zustand react-hook-form zod @hookform/resolvers lucide-react recharts date-fns clsx tailwind-merge
   ```
5. Install development dependencies:
   ```bash
   npm install -D @types/node @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw playwright @playwright/test
   ```
6. Initialize shadcn/ui (Tailwind v3 mode):
   ```bash
   npx shadcn@latest init
   ```
   - Select Vite, React, TypeScript, base color `slate` or `neutral`.
   - Configure `tsconfig.json` path alias `@/*` → `src/*`.
7. Configure `vite.config.ts` with `@/` alias and Vitest test config.
8. Configure `tailwind.config.ts` content paths and custom brand colors.
9. Configure `postcss.config.js` with Tailwind and autoprefixer.
10. Create `src/styles/index.css` with brand CSS variables and Tailwind directives.
11. Create `.env.example`:
    ```text
    VITE_API_BASE_URL=http://localhost:8000
    ```
12. Create `index.html` title: "INTERPROBE MergenVision".
13. Run baseline verification.

**Verification:**

```bash
cd frontend
npm run typecheck   # exit 0
npm run build       # exit 0
npm run lint        # exit 0 (or no lint errors after setup)
```

---

## Task 2 — Design Tokens, Layout, and Routing Shell

**Goal:** Build the app shell, theme provider, navigation, and route tree.

### Files to create

- `src/lib/utils.ts` — `cn()` helper, formatters.
- `src/lib/media.ts` — media URL builder.
- `src/stores/authStore.ts` — Zustand auth token + sidebar/theme state.
- `src/components/layout/Sidebar.tsx`
- `src/components/layout/Topbar.tsx`
- `src/components/layout/Layout.tsx`
- `src/components/layout/ThemeToggle.tsx`
- `src/components/layout/MobileSidebar.tsx`
- `src/routes/index.tsx` — `createBrowserRouter` with `LoginPage`, protected `Layout`, and nested pages.
- `src/App.tsx` — providers (`QueryClientProvider`, `RouterProvider`, `ThemeProvider`, `Sonner`).
- `src/main.tsx` — entry point.

### Steps

1. Add `Inter` font import in `index.css`.
2. Implement dark/light theme toggle using a class on `<html>`; default dark.
3. Build `Sidebar` with nav links, active state, collapse on desktop, overlay on mobile.
4. Build `Topbar` with logo, mobile menu trigger, theme toggle, token display placeholder.
5. Wire up `createBrowserRouter`:
   - `Layout` route wraps all authenticated pages; `LoginPage` is public.
   - Use a simple route guard that checks token presence and redirects to `/login`.
6. Write tests for `cn()`, `formatDate`, `formatMaskedId`, theme toggle, and route helpers.

**Verification:**

```bash
npm run test        # layout/util tests pass
npm run typecheck   # pass
npm run build       # pass
```

---

## Task 3 — API Client, Types, and Base Hooks

**Goal:** Type-safe API layer with axios and TanStack Query defaults.

### Files to create

- `src/api/client.ts` — axios instance + auth interceptor + error normalization.
- `src/api/types.ts` — DTO types from `API_CONTRACT.md`.
- `src/api/people.ts`
- `src/api/photos.ts`
- `src/api/identify.ts`
- `src/api/requests.ts`
- `src/api/audit.ts`
- `src/api/stats.ts`
- `src/api/health.ts`
- `src/api/media.ts`

### Steps

1. Define shared error class `ApiError` with status/message/validation details.
2. Implement request helpers: `get`, `post`, `patch`, `deleteMultipart` (for `multipart/form-data`).
3. Map every Phase 1 endpoint to typed functions.
4. Write unit tests for `client.ts` using MSW.

**Verification:**

```bash
npm run test        # API client tests pass
npm run typecheck   # pass
```

---

## Task 4 — Core UI Components

**Goal:** Install needed shadcn/ui primitives and build custom components on top.

### shadcn/ui components to install

```bash
npx shadcn@latest add button input label card sheet dialog table tabs badge avatar select slider sonner dropdown-menu skeleton separator tooltip breadcrumb command calendar popover checkbox textarea
```

### Custom components to create

- `src/components/ui/StatCard.tsx`
- `src/components/ui/DataTable.tsx`
- `src/components/ui/Pagination.tsx`
- `src/components/ui/FileUploadZone.tsx`
- `src/components/ui/ImagePreview.tsx`
- `src/components/ui/EmptyState.tsx`
- `src/components/ui/PageHeader.tsx`
- `src/components/ui/MaskedId.tsx`

### Steps

1. Create each custom component following design tokens.
2. Add `data-testid` for tests.
3. Write unit tests for `StatCard`, `DataTable`, `Pagination`, `FileUploadZone`, `ImagePreview`, `EmptyState`, `MaskedId`.

**Verification:**

```bash
npm run test        # component tests pass
npm run typecheck   # pass
```

---

## Task 5 — Authentication Feature

**Goal:** Mock token login.

### Files to create

- `src/features/auth/components/LoginForm.tsx`
- `src/features/auth/hooks/useAuth.ts`
- `src/pages/LoginPage.tsx`

### Steps

1. `LoginForm` uses react-hook-form + Zod.
2. On submit, store token in Zustand + `localStorage`.
3. Axios interceptor reads token from Zustand store.
4. Protected route wrapper redirects to `/login` when token missing.

**Verification:**

```bash
npm run test        # login form tests pass
npm run build       # pass
```

---

## Task 6 — People Feature

**Goal:** People list, create, detail, photo gallery, and enroll.

### Files to create

- `src/features/people/schemas.ts`
- `src/features/people/components/PeopleTable.tsx`
- `src/features/people/components/PersonForm.tsx`
- `src/features/people/components/PersonInfoCard.tsx`
- `src/features/people/components/PhotoGallery.tsx`
- `src/features/people/hooks/usePeople.ts`
- `src/features/people/hooks/usePerson.ts`
- `src/features/people/hooks/useCreatePerson.ts`
- `src/features/people/hooks/useUpdatePerson.ts`
- `src/features/people/hooks/useDeletePerson.ts`
- `src/features/people/hooks/usePhotos.ts`
- `src/features/people/hooks/useEnrollPhoto.ts`
- `src/features/people/hooks/useDeletePhoto.ts`
- `src/pages/PeopleListPage.tsx`
- `src/pages/AddPersonPage.tsx`
- `src/pages/PersonDetailPage.tsx`
- `src/pages/EnrollPhotoPage.tsx`

### Steps

1. Implement TanStack Query hooks for people and photo endpoints.
2. Build `PeopleListPage` with search, table, pagination, delete confirmation.
3. Build `AddPersonPage` with person form + optional photo upload.
4. Build `PersonDetailPage` with info card, tabs, photo grid, lightbox, and delete actions.
5. Build `EnrollPhotoPage` with dropzone, preview, detection overlay, result panel.
6. Write MSW integration and component tests for flows.

**Verification:**

```bash
npm run test        # people feature tests pass
npm run typecheck   # pass
```

---

## Task 7 — Identify & Identification Requests Features

**Goal:** Upload identification, show results, and browse request history.

### Files to create

- `src/features/identify/schemas.ts`
- `src/features/identify/components/IdentifyForm.tsx`
- `src/features/identify/components/IdentifyResults.tsx`
- `src/features/identify/components/CandidateCard.tsx`
- `src/features/identify/components/FaceResultCard.tsx`
- `src/features/identify/components/DetectionOverlay.tsx`
- `src/features/identify/components/QualityScore.tsx`
- `src/features/identify/hooks/useIdentify.ts`
- `src/features/requests/hooks/useIdentificationRequests.ts`
- `src/features/requests/hooks/useIdentificationRequest.ts`
- `src/features/requests/components/RequestTable.tsx`
- `src/pages/IdentifyPage.tsx`
- `src/pages/IdentificationRequestsPage.tsx`
- `src/pages/IdentificationRequestDetailPage.tsx`

### Steps

1. Build `IdentifyPage` with upload, topK slider, threshold input, submit.
2. Build result components showing query face crops and candidate cards.
3. Build `IdentificationRequestsPage` with filters and table.
4. Build detail page showing request summary, query image, and ranked candidates.
5. Add tests for identify submission and request list rendering.

**Verification:**

```bash
npm run test        # identify + requests tests pass
npm run typecheck   # pass
```

---

## Task 8 — Dashboard

**Goal:** Operational overview with stats and recent activity.

### Files to create

- `src/features/dashboard/components/StatsGrid.tsx`
- `src/features/dashboard/components/RecentRequests.tsx`
- `src/features/dashboard/components/QuickActions.tsx`
- `src/features/dashboard/hooks/useStats.ts`
- `src/pages/DashboardPage.tsx`

### Steps

1. Fetch `/stats` and `/identification-requests` (latest 5) with TanStack Query.
2. Render 4 stat cards and recent requests mini-table.
3. Add quick-action buttons linking to people/identify/audit/health.
4. Optional: simple bar/line chart for request volume if enough data.
5. Write tests for stat cards and dashboard rendering.

**Verification:**

```bash
npm run test        # dashboard tests pass
npm run typecheck   # pass
```

---

## Task 9 — Audit Log

**Goal:** Queryable audit history.

### Files to create

- `src/features/audit/components/AuditFilters.tsx`
- `src/features/audit/components/AuditTable.tsx`
- `src/features/audit/components/AuditMetadataTree.tsx`
- `src/features/audit/hooks/useAuditLogs.ts`
- `src/pages/AuditPage.tsx`

### Steps

1. Build filters for entityType, action, entityId, date range.
2. Render audit table with expandable `safeMetadata` JSON tree.
3. Add pagination.
4. Write MSW tests for filtering and rendering.

**Verification:**

```bash
npm run test        # audit tests pass
npm run typecheck   # pass
```

---

## Task 10 — System Health

**Goal:** Monitor backend readiness and engine status.

### Files to create

- `src/features/health/components/StatusCard.tsx`
- `src/features/health/components/EngineInfo.tsx`
- `src/features/health/hooks/useHealth.ts`
- `src/pages/SystemHealthPage.tsx`

### Steps

1. Poll `/health` and `/ready`.
2. Show dependency status cards (PostgreSQL, Qdrant, MinIO, TensorRT Runtime).
3. Display engine file lists and GPU usage placeholder.
4. Add refresh button.
5. Write a smoke test.

**Verification:**

```bash
npm run test        # health smoke test passes
npm run typecheck   # pass
```

---

## Task 11 — Error Handling, 404, and Shared States

**Goal:** Polish UX with consistent loading/error/empty states.

### Files to create

- `src/components/shared/LoadingState.tsx`
- `src/components/shared/ErrorState.tsx`
- `src/pages/NotFoundPage.tsx`

### Steps

1. Create reusable `LoadingState` and `ErrorState` components.
2. Apply them across pages.
3. Create 404 page with return link.
4. Ensure all routes have sensible fallbacks.

**Verification:**

```bash
npm run test        # pass
npm run build       # pass
```

---

## Task 12 — E2E Tests with Playwright

**Goal:** Critical user journeys covered end-to-end.

### Files to create

- `playwright.config.ts`
- `e2e/auth.spec.ts`
- `e2e/people-flow.spec.ts`
- `e2e/identify-flow.spec.ts`
- `e2e/navigation.spec.ts`

### Steps

1. Configure Playwright with `baseURL` from env.
2. Use MSW or real backend for data; prefer deterministic mock data.
3. Cover:
   - Login → Dashboard.
   - Create person → view detail.
   - Enroll photo → verify sample metadata.
   - Identify upload → verify result cards.
   - Sidebar navigation to audit/health.

**Verification:**

```bash
npx playwright test
```

---

## Task 13 — Final Verification

**Goal:** All gates pass.

### Commands

```bash
cd /home/user/MergenVision/frontend
npm install
npm run typecheck
npm run build
npm run lint
npm run test
npx playwright test
```

### Acceptance Criteria

- All commands exit 0.
- No `console.error` from tests.
- No Phase 2 routes or components present.
- No raw PII or embedding displayed.
- `git status` shows only `frontend/`, UI docs, and `UI_REFERENCE_CHECK.md` touched.

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| shadcn/ui CLI latest defaults to Tailwind v4 | Pin Tailwind v3 first; use `npx shadcn@latest init --legacy-peer-deps` if needed or install components manually. |
| Existing React 19 dependencies conflict | Delete `node_modules` and lock files; reinstall from scratch under React 18. |
| MSW + Playwright test flakiness | Use deterministic mocks and explicit loading-state waits. |
| Large bundle due to charts | Only import needed recharts components; lazy-load if necessary. |
| backend/Docker changes | Out of scope; do not touch. |
