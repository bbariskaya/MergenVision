import { test, expect } from '@playwright/test'
import { login, logout } from './helpers'

test('login redirects to dashboard and logout returns to login', async ({ page }) => {
  await login(page)
  await expect(page.getByTestId('stat-person-count')).toBeVisible()
  await logout(page)
})
