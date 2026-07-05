# Phase 1 UI Hardening + Playwright E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish Phase 1 frontend by adding accessibility/focus improvements, extracting shared face-result/metadata components, and adding Playwright E2E coverage for the main operator journeys.

**Architecture:** Keep the existing React Router + TanStack Query + MSW + Tailwind/shadcn stack. New shared components (`FaceResult`, `MetadataTree`) live alongside existing UI primitives. Playwright runs against the local Vite dev server where MSW already provides mock data and mock authentication.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS v3, shadcn/ui, React Router v6, TanStack Query v5, MSW v2, Vitest, Playwright, Lucide icons, Zustand.

## Global Constraints
- Only Phase 1 routes/tables; no `/videos`, `/imports`, `/faces`, `/oracle`, `/objects`, `/streams`.
- Keep InterProbe dark brand theme: `#191828` background, `#007BFF` primary, cyan accent, Inter font, white foreground.
- No new API endpoints or backend changes.
- No light mode.
- No `git commit` unless explicitly requested.
- All verification commands must pass before reporting completion.

---

### Task 1: Extract shared `FaceResult` component

**Files:**
- Create: `frontend/src/components/FaceResult.tsx`
- Modify: `frontend/src/pages/IdentifyPage.tsx`
- Modify: `frontend/src/pages/IdentificationRequestDetailPage.tsx`
- Test: `frontend/src/components/FaceResult.test.tsx`

**Interfaces:**
- Consumes: `IdentifyFace`, `IdentifyCandidate` types from `frontend/src/api/types.ts`; `formatScore` from `@/lib/formatters`.
- Produces: `FaceResult({ face, showCandidatesLabel? })`, `CandidateCard({ candidate, isMain? })`, `DecisionBadge({ decision })` components.

```tsx
// frontend/src/components/FaceResult.tsx
import { Link } from 'react-router-dom'
import { User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatScore } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { IdentifyCandidate, IdentifyFace } from '@/api/types'

export function DecisionBadge({ decision }: { decision: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        decision === 'matched' && 'bg-emerald-500/10 text-emerald-500',
        decision === 'possible_match' && 'bg-amber-500/10 text-amber-500',
        decision === 'no_match' && 'bg-destructive/10 text-destructive'
      )}
      data-testid="decision-badge"
    >
      {decision === 'matched' && 'Eşleşti'}
      {decision === 'possible_match' && 'Olası Eşleşme'}
      {decision === 'no_match' && 'Eşleşme Yok'}
      {!['matched', 'possible_match', 'no_match'].includes(decision) && decision}
    </span>
  )
}

export function CandidateCard({ candidate, isMain }: { candidate: IdentifyCandidate; isMain?: boolean }) {
  const Wrapper = candidate.personId ? Link : 'div'
  return (
    <Card className={cn('border-border bg-card', isMain && 'border-primary/50')}>
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-muted">
          <User className="h-6 w-6 text-muted-foreground" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">
            <Wrapper
              to={candidate.personId ? `/people/${candidate.personId}` : undefined}
              className={cn(candidate.personId && 'hover:underline')}
            >
              {candidate.name}
            </Wrapper>
          </p>
          <p className="text-xs text-muted-foreground">
            Skor: {formatScore(candidate.score)} • Sıra: {candidate.rank}
          </p>
        </div>
        <DecisionBadge decision={candidate.decision} />
      </CardContent>
    </Card>
  )
}

export interface FaceResultProps {
  face: IdentifyFace
  title?: string
  showCandidatesLabel?: boolean
}

export function FaceResult({ face, title, showCandidatesLabel = true }: FaceResultProps) {
  const best = face.candidates[0]
  return (
    <Card className="border-border bg-card" data-testid="face-result">
      <CardHeader>
        <CardTitle className="text-base">{title ?? 'Yüz Sonucu'}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">Kalite Skoru</p>
            <p className="font-medium">{formatScore(face.qualityScore)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Karar</p>
            <DecisionBadge decision={face.result.status} />
          </div>
        </div>
        {best ? (
          <div className="space-y-3">
            <p className="text-sm font-medium">{showCandidatesLabel ? 'En İyi Aday' : 'Adaylar'}</p>
            <CandidateCard candidate={best} isMain />
            {showCandidatesLabel && face.candidates.length > 1 && (
              <>
                <p className="text-sm font-medium">Diğer Adaylar</p>
                <div className="space-y-2">
                  {face.candidates.slice(1).map((candidate) => (
                    <CandidateCard key={candidate.rank} candidate={candidate} />
                  ))}
                </div>
              </>
            )}
          </div>
        ) : (
          <Card className="border-border bg-card">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-muted">
                <User className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">Bilinmeyen kişi</p>
                <p className="text-xs text-muted-foreground">Veritabanında eşleşen kayıt bulunamadı.</p>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 1:** Create `frontend/src/components/FaceResult.tsx` with the code above.
- [ ] **Step 2:** Remove the local `DecisionBadge`, `CandidateCard`, and `FaceResult` definitions from `frontend/src/pages/IdentifyPage.tsx` and import from `@/components/FaceResult`.
- [ ] **Step 3:** Remove the local definitions from `frontend/src/pages/IdentificationRequestDetailPage.tsx` and import shared `FaceResult`. Keep the page's surrounding layout.
- [ ] **Step 4:** Run `npm run typecheck` in `frontend/`. Expected: no errors.
- [ ] **Step 5:** Run `npm run test -- --run` in `frontend/`. Expected: existing tests pass.

---

### Task 2: Extract and enhance `MetadataTree`

**Files:**
- Create: `frontend/src/components/ui/MetadataTree.tsx`
- Modify: `frontend/src/pages/AuditLogPage.tsx`
- Test: `frontend/src/components/ui/MetadataTree.test.tsx`

**Interfaces:**
- Consumes: `Record<string, unknown>` metadata object.
- Produces: `MetadataTree({ metadata })` component with expand/collapse and copy JSON.

```tsx
// frontend/src/components/ui/MetadataTree.tsx
import { useState } from 'react'
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export interface MetadataTreeProps {
  metadata: Record<string, unknown>
}

export function MetadataTree({ metadata }: MetadataTreeProps) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)
  const text = JSON.stringify(metadata, null, 2)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="rounded-md bg-muted p-2" data-testid="metadata-tree">
      <div className="flex items-center justify-between gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-auto p-0 text-xs font-normal"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? <ChevronUp className="mr-1 h-3 w-3" /> : <ChevronDown className="mr-1 h-3 w-3" />}
          Metadata
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleCopy}
          aria-label="Metadata JSON kopyala"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
        </Button>
      </div>
      {expanded && (
        <pre className="mt-2 max-h-48 overflow-auto rounded border border-border bg-card p-2 text-xs">
          {text}
        </pre>
      )}
    </div>
  )
}
```

- [ ] **Step 1:** Create `frontend/src/components/ui/MetadataTree.tsx` with the code above.
- [ ] **Step 2:** In `frontend/src/pages/AuditLogPage.tsx`, remove the local `MetadataTree` function and import `MetadataTree` from `@/components/ui/MetadataTree`.
- [ ] **Step 3:** Run `npm run typecheck` in `frontend/`. Expected: no errors.
- [ ] **Step 4:** Run `npm run test -- --run` in `frontend/`. Expected: existing tests pass.

---

### Task 3: Sidebar active state + focus/reduced-motion globals

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- No new exported code; `Sidebar` behavior changes visually.

```tsx
// frontend/src/components/layout/Sidebar.tsx nav item className replacement
className={({ isActive }) =>
  cn(
    'relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    isActive
      ? 'bg-primary text-primary-foreground before:absolute before:left-0 before:top-1/2 before:h-6 before:w-1 before:-translate-y-1/2 before:rounded-r-full before:bg-primary-foreground'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
  )
}
```

```css
/* frontend/src/index.css additions inside @layer base :root block */
html {
  scroll-behavior: smooth;
}

:focus-visible {
  @apply outline-none ring-2 ring-primary ring-offset-2 ring-offset-background;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 1:** Update sidebar nav item className as shown above.
- [ ] **Step 2:** Add global focus and reduced-motion styles to `frontend/src/index.css`.
- [ ] **Step 3:** Run `npm run typecheck`. Expected: no errors.
- [ ] **Step 4:** Run `npm run lint`. Expected: only the 2 existing shadcn variant warnings.

---

### Task 4: Playwright setup

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/.env.e2e.example`
- Modify: `frontend/.gitignore` (if it exists, append `test-results/` and `playwright-report/`)

**Interfaces:**
- Playwright config exposes `baseURL`, `webServer`, and one Chromium project.

```ts
// frontend/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
```

```bash
# frontend/.env.e2e.example
PLAYWRIGHT_BASE_URL=http://localhost:5173
```

- [ ] **Step 1:** Install Playwright browsers: `npx playwright install chromium` (also run `--with-deps` if CI).
- [ ] **Step 2:** Create `frontend/playwright.config.ts` as above.
- [ ] **Step 3:** Create `frontend/.env.e2e.example` as above.
- [ ] **Step 4:** Add `test-results/` and `playwright-report/` to `frontend/.gitignore`.
- [ ] **Step 5:** Verify config loads: `npx playwright test --list`. Expected: 0 tests listed, no config errors.

---

### Task 5: Playwright E2E tests

**Files:**
- Create: `frontend/e2e/auth.spec.ts`
- Create: `frontend/e2e/navigation.spec.ts`
- Create: `frontend/e2e/people.spec.ts`
- Create: `frontend/e2e/identify.spec.ts`
- Create: `frontend/e2e/requests.spec.ts`
- Create: `frontend/e2e/audit.spec.ts`
- Create: `frontend/e2e/health.spec.ts`

**Interfaces:**
- Tests import `@playwright/test`, use `data-testid` selectors, log in via the login form, and assert page content.

```ts
// frontend/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test('login redirects to dashboard and logout to login', async ({ page }) => {
  await page.goto('/login')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await expect(page).toHaveURL('/')
  await expect(page.getByTestId('stat-person-count')).toBeVisible()
  await page.getByTestId('logout-button').click()
  await expect(page).toHaveURL(/\/login$/)
})
```

```ts
// frontend/e2e/navigation.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await expect(page).toHaveURL('/')
})

test('can navigate to all Phase 1 routes via sidebar', async ({ page }) => {
  const routes = [
    { label: 'People', path: '/people' },
    { label: 'Identify', path: '/identify' },
    { label: 'Identification Requests', path: '/identification-requests' },
    { label: 'Audit Log', path: '/audit' },
    { label: 'System Health', path: '/health' },
  ]
  for (const route of routes) {
    await page.getByRole('navigation').getByRole('link', { name: route.label }).click()
    await expect(page).toHaveURL(route.path)
  }
})
```

```ts
// frontend/e2e/people.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await page.goto('/people')
})

test('people page loads and shows table', async ({ page }) => {
  await expect(page.getByTestId('people-table')).toBeVisible()
})

test('create new person opens dialog and closes', async ({ page }) => {
  await page.getByRole('button', { name: 'Yeni Kişi Ekle' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByLabel('Ad').fill('E2E')
  await page.getByLabel('Soyad').fill('Tester')
  await page.getByLabel('TC Kimlik No').fill('12345678901')
  await page.getByRole('button', { name: 'Kaydet' }).click()
  await expect(page.getByRole('dialog')).not.toBeVisible()
})
```

```ts
// frontend/e2e/identify.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await page.goto('/identify')
})

test('identify page renders upload zone and triggers result', async ({ page }) => {
  await expect(page.getByTestId('identify-upload-zone')).toBeVisible()
  await page.getByTestId('identify-upload-zone').setInputFiles({
    name: 'face.png',
    mimeType: 'image/png',
    buffer: Buffer.from('mock-image'),
  })
  await page.getByTestId('identify-button').click()
  await expect(page.getByTestId('decision-badge').first()).toBeVisible({ timeout: 5000 })
})
```

```ts
// frontend/e2e/requests.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await page.goto('/identification-requests')
})

test('requests list loads and detail page opens', async ({ page }) => {
  await expect(page.getByTestId('requests-table')).toBeVisible()
  await page.getByTestId('requests-table').getByRole('link').first().click()
  await expect(page).toHaveURL(/\/identification-requests\//)
  await expect(page.getByTestId('decision-badge').first()).toBeVisible()
})
```

```ts
// frontend/e2e/audit.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await page.goto('/audit')
})

test('audit log table is visible and metadata can expand', async ({ page }) => {
  await expect(page.getByTestId('audit-log-table')).toBeVisible()
  await page.getByTestId('metadata-tree').first().getByRole('button', { name: 'Metadata' }).click()
  await expect(page.getByTestId('metadata-tree').first().locator('pre')).toBeVisible()
})
```

```ts
// frontend/e2e/health.spec.ts
import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await page.goto('/health')
})

test('health page shows system status', async ({ page }) => {
  await expect(page.getByText('Sistem Durumu')).toBeVisible()
})
```

- [ ] **Step 1:** Add missing `data-testid` selectors in source code if any (login inputs/button, logout button, requests table).
- [ ] **Step 2:** Create each spec file above.
- [ ] **Step 3:** Run `npx playwright test` in `frontend/`. Expected: all tests pass.

---

### Task 6: Final verification

- [ ] **Step 1:** Run `npm run typecheck` in `frontend/`. Expected: no errors.
- [ ] **Step 2:** Run `npm run lint` in `frontend/`. Expected: only existing 2 warnings.
- [ ] **Step 3:** Run `npm run test -- --run` in `frontend/`. Expected: 26 passing.
- [ ] **Step 4:** Run `npm run build` in `frontend/`. Expected: success.
- [ ] **Step 5:** Run `npx playwright test` in `frontend/`. Expected: all E2E tests pass.
