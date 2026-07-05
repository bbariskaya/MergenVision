import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
  await page.goto('/people')
})

test('people page loads and shows table', async ({ page }) => {
  await expect(page.getByTestId('people-table')).toBeVisible({ timeout: 10000 })
})

test('create new person opens dialog and closes after submit', async ({ page }) => {
  await page.getByRole('button', { name: 'Yeni Kişi Ekle' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByLabel('Ad', { exact: true }).fill('E2E')
  await page.getByLabel('Soyad', { exact: true }).fill('Tester')
  await page.getByLabel('TC Kimlik No', { exact: true }).fill('11111111111')
  await page.getByRole('button', { name: 'Kaydet' }).click()
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(page.getByTestId('people-table')).toBeVisible()
})
