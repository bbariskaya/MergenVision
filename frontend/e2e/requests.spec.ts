import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
  await page.goto('/identification-requests')
})

test('requests list loads and detail page opens', async ({ page }) => {
  await expect(page.getByTestId('identification-requests-table')).toBeVisible()
  const firstRow = page.getByTestId('identification-requests-table').getByRole('row').nth(1)
  await firstRow.getByRole('cell').nth(1).click()
  await expect(page).toHaveURL(/\/identification-requests\//)
  await expect(page.getByTestId('decision-badge').first()).toBeVisible()
})
