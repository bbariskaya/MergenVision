import { expect, type Page } from '@playwright/test'

export async function login(page: Page) {
  await page.goto('/login')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByTestId('login-token-input').fill('admin-token')
  await page.getByTestId('login-submit-button').click()
  await expect(page).toHaveURL('/')
}

export async function logout(page: Page) {
  await page.getByTestId('logout-button').click()
  await expect(page).toHaveURL(/\/login$/)
}
