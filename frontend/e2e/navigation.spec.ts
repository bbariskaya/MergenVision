import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
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

  await page.getByRole('navigation').getByRole('link', { name: 'Dashboard' }).click()
  await expect(page).toHaveURL('/')
})
