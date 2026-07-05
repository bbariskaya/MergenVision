# MergenVision Phase 1 — UI/UX Design Specification

> Version: 2026-07-04  
> Scope: Phase 1 admin/operations panel only. No Phase 2 routes (videos, imports, oracle, faces, objects, streams).  
> Brand: INTERPROBE Bilgi Teknolojileri A.Ş.

## 1. Goal

Build a professional, operator-friendly, dark-mode-first React admin panel for the MergenVision face-recognition platform. The UI must be scoped to Phase 1 endpoints, INTERPROBE branded, accessible, and responsive.

## 2. Constraints

- Only Phase 1 routes/tables from `API_CONTRACT.md` and `DATA_MODEL.md`.
- No `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams` routes or cards.
- National ID is captured only at creation; UI always displays `nationalIdMasked` (`******8901`).
- No raw embeddings, hashes, or image bytes stored in UI state.
- All images fetched through `/media/{bucket}/{objectKey}`.
- No git add/commit/push.

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build tool | Vite 5/6 |
| Styling | Tailwind CSS v3 |
| Component base | shadcn/ui (Radix + Tailwind) |
| Routing | react-router-dom v6 |
| Server state | @tanstack/react-query v5 |
| HTTP client | axios |
| Client state | zustand |
| Forms | react-hook-form + zod + @hookform/resolvers |
| Icons | lucide-react |
| Charts (dashboard) | recharts |
| Tests | vitest + @testing-library/react + MSW |
| E2E | playwright |
| Date formatting | date-fns |

## 4. Brand Identity

- Company: **INTERPROBE Bilgi Teknolojileri A.Ş.**
- Slogan: **Protect Beyond The Endpoint**
- Sector feel: trust, operational seriousness, cyber defense.
- Logo: `https://interprobe.com.tr/themes/interprobe/assets/img/logo.png`
- Favicon: `https://interprobe.com.tr/themes/interprobe/assets/img/fav/android-icon-192x192.png`

### Color Tokens

```css
--bg-primary:    #191828;
--bg-secondary:  #232336;
--bg-card:       #232336;
--bg-elevated:   #2d2d45;
--bg-hover:      #334155;
--border:        #3a3a55;
--text-primary:  #ffffff;
--text-secondary:#a0a3bd;
--text-muted:    #64748b;
--accent:        #007bff;
--accent-hover:  #0056b3;
--accent-glow:   rgba(0, 123, 255, 0.2);
--success:       #22c55e;
--warning:       #f59e0b;
--danger:        #ef4444;
--info:          #0ea5e9;
```

### Typography

- Font: `Inter`, system-ui fallback.
- H1: 1.75rem / semibold
- H2: 1.5rem / semibold
- H3: 1.25rem / semibold
- Body: 0.875rem / normal
- Small: 0.75rem

### Spacing & Radius

- Page padding: `p-6`
- Card padding: `p-4` / `p-6`
- Gap: `gap-4` / `gap-6`
- Radius: `rounded-lg` (8px), `rounded-xl` (12px)
- Shadow: `shadow-lg shadow-slate-900/50`

## 5. Layout

- App shell: fixed `Sidebar` (left, 16rem) + `TopBar` (top, sticky) + scrollable `Main`.
- Mobile: sidebar becomes an overlay triggered by hamburger menu; topbar remains.
- Breadcrumbs below topbar on detail pages.
- Content max-width: `max-w-7xl` centered.

### Navigation (Sidebar)

- Dashboard → `/`
- People → `/people`
- Identify → `/identify`
- Identification Requests → `/identification-requests`
- Audit Log → `/audit`
- System Health → `/health`

## 6. Route & Page Mapping

| Route | Page | Notes |
|---|---|---|
| `/login` | LoginPage | Mock token input; stores token in localStorage + Zustand. |
| `/` | DashboardPage | Stats cards, recent requests, quick actions, simple trend charts. |
| `/people` | PeopleListPage | Paginated table, search, add person, row actions. |
| `/people/new` | AddPersonPage | Create person form; optional first photo upload. |
| `/people/:personId` | PersonDetailPage | Info card, tabs: Photos / Details / Activity, photo grid. |
| `/people/:personId/photos/enroll` | EnrollPhotoPage | Drag-drop upload + enrollment result panel. |
| `/identify` | IdentifyPage | Upload, threshold/topK settings, result cards. |
| `/identification-requests` | IdentificationRequestsPage | Paginated list with filters. |
| `/identification-requests/:requestId` | IdentificationRequestDetailPage | Request summary, query image, face/candidate cards. |
| `/audit` | AuditPage | Filterable audit log table. |
| `/health` | SystemHealthPage | Dependency status cards, engine info, GPU usage. |
| `*` | NotFoundPage | 404 link back to dashboard. |

## 7. Page Specifications

### 7.1 Login Page (`/login`)

- Left side: INTERPROBE logo + "INTERPROBE MergenVision" + tagline.
- Right side: simple form with token input and "Oturum Aç" button.
- Saves token to Zustand + `localStorage`; axios interceptor reads it.
- No real authentication backend for Phase 1.

### 7.2 Dashboard (`/`)

- 4 stat cards: Toplam Kişi, Toplam Fotoğraf, Yüz Örneği, Tanıma İsteği.
- Recent identification requests table (last 5).
- Quick actions: "Yeni Kişi Ekle", "Yüz Tanıma Yap", "Tüm İstekleri Gör", "Audit Log".
- Optional mini charts for request volume over 7 days if enough data.

### 7.3 People List (`/people`)

- Title + "Yeni Kişi Ekle" button + search input.
- DataTable columns: Ad Soyad, Maskelenmiş TC, Fotoğraf Sayısı, Sample Sayısı, Durum, İşlemler.
- Pagination.
- Row actions: Görüntüle, Düzenle, Sil (confirm modal).
- Name click navigates to detail.

### 7.4 Add/Edit Person (`/people/new`, future edit modal)

- Fields: firstName, lastName, nationalId, details (key/value JSON/text), isActive.
- Optional photo upload on creation.
- Validation with Zod; inline errors.

### 7.5 Person Detail (`/people/:personId`)

- Person card: avatar/initials, full name, masked TC, status badge, created at, details JSON tree.
- Tabs: Photos | Details | Activity (activity can use audit log filtered by `entityId=personId`).
- Photos grid: thumbnail from `/media/people-photos/...`, upload date, sample count, delete action.
- Lightbox on thumbnail click.
- Action buttons: Fotoğraf Yükle, Düzenle, Kişiyi Sil.

### 7.6 Enroll Photo (`/people/:personId/photos/enroll`)

- Left: dropzone + selected image preview.
- If a face is detected, draw bounding box overlay (using returned `boundingBox`).
- Right: result panel after submit.
  - Success: message, sampleId, qdrantPointId, model/version, qualityScore, crop preview.
  - Errors: no face, multiple faces, validation/file too large.
- Buttons: "Görsel Yükle", "İptal", "Başka Fotoğraf Yükle".

### 7.7 Identify (`/identify`)

- Upload zone.
- Settings: topK slider (1–20, default 5), threshold number input (optional).
- If multiple faces detected, `selectedFaceIndex` dropdown.
- Submit → `POST /identify`.
- Results: one card per query face showing crop, quality score, best match (large) + alternative candidates (small).
- Match card: person name, decision badge (`matched`, `possible_match`, `no_match`), score, threshold, sample photo, link to person detail.

### 7.8 Identification Requests (`/identification-requests`)

- Filters: decision badge, date range.
- DataTable columns: ID (shortened), Tarih, Karar badge, Yüz Sayısı, topK, Detay.
- Pagination.
- Row action: Detay → navigate to detail page.

### 7.9 Identification Request Detail (`/identification-requests/:requestId`)

- Summary card: request ID, status, decision, face count, threshold, completedAt, error message if failed.
- Left: query image preview.
- Right: face cards, each with crop, bounding box, quality score, candidate list.
- Candidate: rank, name, sampleId, score, decision badge.

### 7.10 Audit Log (`/audit`)

- Filters: entityType dropdown, action search, entityId search, date range.
- DataTable columns: Zaman, Aksiyon, Entity Type, Entity ID, Actor, Outcome, safeMetadata (expandable JSON tree).
- Pagination.

### 7.11 System Health (`/health`)

- 4 status cards: PostgreSQL, Qdrant, MinIO, TensorRT Runtime.
- Engine info: SCRFD engine files, ArcFace engine files, GPU name, GPU memory bar.
- Action buttons: Yenile, "Engine'leri Yeniden Build Et" (danger outline, Phase 2 / manual; UI just shows button).

## 8. Component Inventory

### shadcn/ui Base Components to Install

Button, Input, Label, Card, Sheet, Dialog, Table, Tabs, Badge, Avatar, Select, Slider, Sonner (toast), DropdownMenu, Skeleton, Separator, Tooltip, Breadcrumb, Command, Calendar, Popover, Checkbox, Textarea.

### Custom Components

```text
components/
├── layout/
│   ├── Sidebar.tsx
│   ├── Topbar.tsx
│   ├── Layout.tsx
│   ├── ThemeToggle.tsx
│   └── MobileSidebar.tsx
├── ui/
│   ├── StatCard.tsx
│   ├── DataTable.tsx
│   ├── Pagination.tsx
│   ├── FileUploadZone.tsx
│   ├── ImagePreview.tsx
│   ├── EmptyState.tsx
│   ├── PageHeader.tsx
│   └── MaskedId.tsx
├── face/
│   ├── FaceResultCard.tsx
│   ├── CandidateCard.tsx
│   ├── DetectionOverlay.tsx
│   └── QualityScore.tsx
└── audit/
    └── AuditMetadataTree.tsx
```

## 9. API Integration

- Base URL: `import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000`).
- `src/api/client.ts`: axios instance with base URL, `Authorization: Bearer <token>` interceptor, serializable request/response error normalization.
- `src/api/*.ts`: people, photos, identify, requests, audit, stats, health, media.
- TanStack Query hooks for reads; mutations invalidate related query keys:
  - `createPerson` → invalidate `['people']`, `['stats']`
  - `enrollPhoto` → invalidate `['people', id, 'photos']`, `['stats']`
  - `deletePerson` / `deletePhoto` → invalidate related lists and stats
  - `identify` → invalidate `['identification-requests']`, `['stats']`

## 10. State Management

- **TanStack Query**: server state (lists, details, stats, health).
- **Zustand**: auth token, sidebar collapse, theme preference.
- **React Hook Form + Zod**: local form state and validation.
- **URL state**: filters, pagination page through query params where useful (optional).

## 11. Forms & Validation

- Zod schemas in `src/features/<domain>/schemas.ts`.
- Person schema: firstName/lastName min length, nationalId 11 digits, details optional JSON.
- Photo upload: file size max 10 MB, MIME image/jpeg or image/png.
- Identify settings: topK 1-20, threshold optional 0–1.
- Server validation errors merged into form state after submit.

## 12. Media Handling

- `ImagePreview` component fetches `/media/{bucket}/{objectKey}` via `<img src>`.
- Image URL helper in `src/lib/media.ts`.
- Loading skeleton and error fallback (broken-image icon).
- No base64 embedded images.

## 13. Accessibility

- Dark mode default; light mode optional via `.light` class on `<html>`.
- Focus-visible rings on all interactive elements.
- All buttons have accessible labels; icon-only buttons use `aria-label`.
- Form inputs linked to labels via `htmlFor`/`id`.
- Dialogs use `role="dialog"`, `aria-modal`, focus trap (handled by Radix Dialog).
- Toast notifications use `role="alert"` (Sonner).
- Color contrast meets WCAG AA for text on surfaces.

## 14. File Structure

```text
frontend/
├── public/
│   └── logo.svg
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── types.ts
│   │   ├── people.ts
│   │   ├── photos.ts
│   │   ├── identify.ts
│   │   ├── requests.ts
│   │   ├── audit.ts
│   │   ├── stats.ts
│   │   └── health.ts
│   ├── components/
│   │   ├── layout/
│   │   ├── ui/
│   │   ├── face/
│   │   └── audit/
│   ├── features/
│   │   ├── auth/
│   │   ├── people/
│   │   ├── identify/
│   │   ├── requests/
│   │   └── audit/
│   ├── hooks/
│   ├── lib/
│   │   ├── utils.ts
│   │   ├── media.ts
│   │   └── formatters.ts
│   ├── pages/
│   ├── routes/
│   │   └── index.tsx
│   ├── stores/
│   │   └── authStore.ts
│   ├── styles/
│   │   └── index.css
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── e2e/
│   └── *.spec.ts
├── tests/
│   └── setup.ts
├── index.html
├── tailwind.config.ts
├── postcss.config.js
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── playwright.config.ts
├── vitest.config.ts (or inside vite.config.ts)
├── .env.example
└── package.json
```

## 15. Testing Strategy

### Unit / Component Tests

- `Button`, `Input`, `Badge`, `StatCard`, `DataTable`, `FileUploadZone`, `ImagePreview`, `Pagination`.
- Formatting utilities: maskedId, formatDate, formatScore.
- API client error normalization.

### Integration Tests (MSW)

- People list renders rows; search filters.
- Add person form submits and invalidates list.
- Enroll photo shows preview and success result.
- Identify flow shows result cards.
- Audit log renders with filters.

### E2E (Playwright)

- Login → Dashboard navigation.
- Create person → enroll photo → verify in person detail.
- Upload identify image → verify candidate cards.
- Navigate audit log.

## 16. Environment Variables

```text
VITE_API_BASE_URL=http://localhost:8000
```

## 17. Verification Gates

Before marking UI work complete:

```bash
cd frontend
npm install
npm run typecheck
npm run build
npm run test
npm run lint
npx playwright test
```

All commands must exit 0.
