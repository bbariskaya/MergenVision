import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
  await page.goto('/health')
})

test('health page shows system status', async ({ page }) => {
  await expect(page.getByTestId('health-status-badge')).toBeVisible()
})
