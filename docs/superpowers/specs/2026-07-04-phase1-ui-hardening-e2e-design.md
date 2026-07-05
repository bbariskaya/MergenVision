# Phase 1 UI Hardening + Playwright E2E Design

> Project: MergenVision Phase 1
> Scope: UI polish, accessibility/focus states, component extraction, Playwright E2E tests

## Goal
Complete the Phase 1 administration/operator UI by adding accessibility hardening, removing duplicated candidate/result UI code, and covering the main Phase 1 user journeys with Playwright E2E tests against the Vite dev server with MSW enabled.

## Constraints
- Only Phase 1 routes and tables; no `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams`.
- Keep the existing InterProbe brand dark theme: `#191828` background, `#007BFF` primary, cyan accent, Inter font, white foreground.
- Do not introduce light mode or change color tokens.
- Use `data-testid` for stable E2E selectors.
- Mock authentication via MSW (`admin-token` stored in `localStorage`).
- Do not store raw national ID or embeddings in the frontend state beyond what the API already returns masked.

## UX Requirements
- Sidebar shows the active route with a primary left border in addition to the existing background highlight.
- All interactive elements have a visible `:focus-visible` ring (`ring-2 ring-primary ring-offset-2 ring-offset-background`).
- Respect `prefers-reduced-motion` by disabling non-essential animations/transitions globally.
- Audit log metadata viewer is extracted into its own component and shows a compact preview with an expand/collapse toggle and a JSON copy action.
- Identify/identification-request detail face results use a single shared component.
- Loading, error, and empty states remain consistent across Phase 1 pages.
- E2E tests cover login flow, navigation/dashboard, people CRUD list/detail, identify submission with mock image, identification requests list/detail, audit log visibility, and system health page load.

## Architecture
- New shared component directory: existing `src/components/ui/` for generic primitives, page-specific result cards live under `src/components/`.
- `FaceResult`, `DecisionBadge`, and `CandidateCard` move from `IdentifyPage.tsx` and `IdentificationRequestDetailPage.tsx` to `src/components/FaceResult.tsx`.
- `MetadataTree` moves from `AuditLogPage.tsx` to `src/components/ui/MetadataTree.tsx`.
- Global accessibility styles live in `src/index.css`.
- Playwright tests live in `frontend/e2e/` with a project-relative `playwright.config.ts`. Tests rely on MSW data already served by the dev server.

## Testing Strategy
- Unit/integrasyon testleri: mevcut `npm run test -- --run` komutu geçmeye devam etmeli.
- Lint: `npm run lint` mevcut 2 shadcn varyant export uyarısı dışında temiz olmalı.
- Typecheck: `npm run typecheck` hatasız geçmeli.
- Build: `npm run build` başarılı olmalı.
- E2E: `npx playwright test` başarılı olmalı (önce `npx playwright install --with-deps chromium` zorunlu).

## Out of Scope
- Light mode or full theming rewrite.
- Video/Phase 2 pages.
- Production backend integration changes.
- Mobile native app.
