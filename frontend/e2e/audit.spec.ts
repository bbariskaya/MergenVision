import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
  await page.goto('/audit')
})

test('audit log table is visible and metadata can expand', async ({ page }) => {
  await expect(page.getByTestId('audit-log-table')).toBeVisible()
  const firstTree = page.getByTestId('metadata-tree').first()
  await firstTree.getByRole('button', { name: 'Toggle metadata' }).click()
  await expect(firstTree.locator('pre')).toBeVisible()
})
