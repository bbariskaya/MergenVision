import { test, expect } from '@playwright/test'
import { login } from './helpers'

test.beforeEach(async ({ page }) => {
  await login(page)
  await page.goto('/identify')
})

test('identify page renders upload zone and triggers result', async ({ page }) => {
  await expect(page.getByTestId('identify-upload-zone')).toBeVisible()
  await page.getByLabel('Dosya yükle').setInputFiles({
    name: 'face.png',
    mimeType: 'image/png',
    buffer: Buffer.from('mock-image'),
  })
  await page.getByTestId('identify-button').click()
  await expect(page.getByTestId('face-result').first()).toBeVisible({ timeout: 5000 })
})
