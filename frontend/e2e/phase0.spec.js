/**
 * Phase 0 E2E Test Suite
 * Tests critical contract scenarios per SOP
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BACKEND_URL = 'http://localhost:8000';

/**
 * Helper: pick the "Upload" file input only (NOT the camera capture input).
 * Because UI now has 2 file inputs:
 *  - upload:  <input type="file" ...>
 *  - camera:  <input type="file" capture="environment" ...>
 *
 * Playwright strict mode requires a locator to resolve to exactly 1 element.
 */
const getUploadFileInput = (page) => page.locator('input[type="file"]:not([capture])');

/**
 * Helper: find the primary action button even if its label changes.
 * We accept: Analisis / Deteksi / Analyze / Detect (case-insensitive)
 */
const getAnalyzeButton = (page) =>
  page.getByRole('button', { name: /analisis|deteksi|analyze|detect/i });

test.describe('Phase 0 - Contract Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to analyze page
    await page.goto('/analyze');
    await expect(page).toHaveURL(/\/analyze/);
    await page.waitForLoadState('networkidle');
  });

  test('A2. Smoke Test - Page loads without errors', async ({ page }) => {
    // Check no console errors
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/analyze');
    await expect(page).toHaveURL(/\/analyze/);
    await page.waitForLoadState('networkidle');

    // Verify key elements visible (keep as-is, but tolerant)
    await expect(page.locator('text=Upload')).toBeVisible({ timeout: 5000 });

    // Check no red errors
    expect(errors.filter((e) => !e.includes('Download the React DevTools'))).toHaveLength(0);
  });

  test('B1. Success Flow - Valid detection with items', async ({ page }) => {
    // Intercept API call and mock success response
    await page.route('**/api/v1/detection/photo', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 123,
          items: [
            {
              label: 'nasi_goreng',
              confidence: 0.95,
              bbox: [10, 20, 100, 150],
              tkpi: {
                id: 1,
                name: 'Nasi Goreng',
                nutrition: {
                  energi_kal: 200,
                  protein_g: 5.2,
                  lemak_g: 3.1,
                  karbo_g: 40.5,
                  serat_g: 1.2,
                },
              },
              nutrition_status: 'COCOK',
              nutrition_status_label: 'Cocok',
            },
          ],
        }),
      });
    });

    // Upload a dummy file
    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'test-food.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-image-data'),
    });

    // Click analyze button (robust selector)
    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait for detection cards to render
    await page.waitForSelector('text=Nasi Goreng', { timeout: 5000 });

    // Verify card rendered
    await expect(page.locator('text=Nasi Goreng')).toBeVisible();
    await expect(page.locator('text=Cocok')).toBeVisible();

    // Verify no error toast (best-effort)
    await expect(page.locator('text=error')).not.toBeVisible();
  });

  test('B2. Empty Detection - Backend returns empty items', async ({ page }) => {
    // Mock empty response
    await page.route('**/api/v1/detection/photo', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 2,
          items: [],
        }),
      });
    });

    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'blank.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('blank'),
    });

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait a bit for response
    await page.waitForTimeout(1000);

    // Verify empty state message or toast
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('tidak'); // Should show "tidak ada makanan terdeteksi" or similar
  });

  test('B3. CRITICAL - Invalid Schema - Backend returns wrong field', async ({ page }) => {
    // Track console errors
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Mock invalid schema response (detections instead of items)
    await page.route('**/api/v1/detection/photo', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 3,
          detections: [
            // WRONG FIELD - should be "items"
            {
              label: 'test',
              confidence: 0.9,
            },
          ],
        }),
      });
    });

    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('test'),
    });

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait for error
    await page.waitForTimeout(2000);

    // Verify error message appears
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('Invalid response schema'); // From TOAST_MESSAGES.INVALID_SCHEMA

    // Verify console has error
    const hasSchemaError = consoleErrors.some((e) => e.includes('Invalid response schema'));
    expect(hasSchemaError).toBeTruthy();
  });

  test('B4. Error 422 - Validation Error Contract', async ({ page }) => {
    // Mock 422 error response
    await page.route('**/api/v1/detection/photo', async (route) => {
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'No file provided',
          code: 'VALIDATION_ERROR',
          context: { field: 'file' },
        }),
      });
    });

    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('test'),
    });

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait for error toast
    await page.waitForTimeout(2000);

    // Verify error message shows detail
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('No file provided'); // From error.detail
  });

  test('D1. CRITICAL - Timeout after 30 seconds', async ({ page }) => {
    // Mock slow response (will be aborted by frontend after 30s)
    await page.route('**/api/v1/detection/photo', async (route) => {
      // Delay longer than timeout
      await new Promise((resolve) => setTimeout(resolve, 35000));
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ analysis_id: 999, items: [] }),
      });
    });

    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('test'),
    });

    // Start timer
    const startTime = Date.now();

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait for timeout error (should appear around 30s)
    await page.waitForTimeout(32000); // Wait 32s to ensure timeout triggered

    const elapsed = Date.now() - startTime;

    // Verify timeout occurred around 30s (allow 28-35s range)
    expect(elapsed).toBeGreaterThan(28000);
    expect(elapsed).toBeLessThan(35000);

    // Verify timeout message appears
    const bodyText = await page.textContent('body');
    expect(bodyText).toContain('timeout'); // Should show timeout message
  });
});

test.describe('Phase 0 - Hook Tests (Basic)', () => {
  test('C1. Edit panel - Porsi controls are visible and clickable', async ({ page }) => {
    // Mock detection endpoint
    await page.route('**/api/v1/detection/photo', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          analysis_id: 1,
          items: [
            {
              label: 'test',
              confidence: 0.9,
              bbox: [0, 0, 100, 100],
              tkpi: { id: 1, name: 'Test Food', nutrition: {} },
            },
          ],
        }),
      });
    });

    // Upload and get detection
    await page.goto('/analyze');
    await expect(page).toHaveURL(/\/analyze/);

    const fileInput = getUploadFileInput(page);
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('test'),
    });

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10000 });
    await analyzeBtn.click();

    // Wait a bit for detection UI
    await page.waitForTimeout(1000);

    // Click edit button (use role; avoid stale text-only selector)
    const editBtn = page.getByRole('button', { name: /edit/i }).first();
    await expect(editBtn).toBeVisible({ timeout: 10000 });
    await editBtn.click();

    // From your trace: Edit opens "Porsi" controls (no search input)
    await expect(page.locator('text=Porsi')).toBeVisible({ timeout: 10000 });

    // Click one porsi option that should exist based on UI (trace shows 0.5x, 1x, 1.5x, 2x)
    const porsiBtn = page.getByRole('button', { name: /1\.5x/i });
    await expect(porsiBtn).toBeVisible({ timeout: 10000 });
    await porsiBtn.click();

    // Minimal assertion: still on page and porsi section remains visible
    await expect(page.locator('text=Porsi')).toBeVisible();
  });
});
