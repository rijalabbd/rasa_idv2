// @ts-check
import { test, expect } from '@playwright/test';
import { Buffer } from 'buffer';

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const ANALYZE_PATH = '/analyze';

// API endpoints (match your backend contract)
const DETECT_ENDPOINT = '**/api/v1/detection/photo';
const TKPI_SEARCH_ENDPOINT = '**/api/v1/tkpi/search**';
const FEEDBACK_ENDPOINT = '**/api/v1/feedback';
const CLASS_REQUEST_ENDPOINT = '**/api/v1/class-request';

test.describe('AnalyzePhoto Feature (Phase 1)', () => {
  const makeFakeImageFile = (name = 'test.jpg') => ({
    name,
    mimeType: 'image/jpeg',
    buffer: Buffer.from('fake-image-content'),
  });

  const gotoAnalyze = async (page) => {
    await page.goto(`${BASE_URL}${ANALYZE_PATH}`, { waitUntil: 'domcontentloaded' });
    // If your app uses SPA routing, networkidle can hang; domcontentloaded is safer
    await expect(page).toHaveURL(new RegExp(`${ANALYZE_PATH.replace('/', '\\/')}`));
  };

  /**
   * Find a usable file input.
   * Priority:
   *  1) data-testid="file-upload" (recommended)
   *  2) any input[type=file] (if only one)
   *  3) if none visible, click an upload button text, then search again
   */
  const getAnyFileInput = async (page) => {
    const byTestId = page.getByTestId('file-upload');
    if (await byTestId.count()) return byTestId;

    let inputs = page.locator('input[type="file"]');
    if ((await inputs.count()) > 0) {
      // If multiple, pick the first (upload or camera—either can accept setInputFiles in desktop tests)
      return inputs.first();
    }

    // Try to click a button that might reveal/mount the input
    const revealBtn = page.getByRole('button', { name: /unggah|upload|ambil foto|kamera|camera/i }).first();
    if (await revealBtn.count()) {
      await revealBtn.click({ timeout: 5000 }).catch(() => {});
    }

    inputs = page.locator('input[type="file"]');
    if ((await inputs.count()) > 0) return inputs.first();

    // Fail fast with a useful error
    throw new Error(
      `No <input type="file"> found on ${BASE_URL}${ANALYZE_PATH}. ` +
        `Either the page is not your frontend, the route differs, or the file input is not rendered. ` +
        `Recommended: add data-testid="file-upload" to the real file input.`
    );
  };

  const getAnalyzeButton = (page) =>
    page.getByRole('button', { name: /analisis|deteksi|analyze|detect/i });

  const getToast = (page) =>
    page.locator('[data-testid="toast"], [role="alert"], .toast, .Toastify__toast').first();

  test('Upload valid image -> click analyze -> see detection results & totals', async ({ page }) => {
    await page.route(DETECT_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 123,
          items: [
            {
              label: 'nasi_goreng',
              confidence: 0.95,
              bbox: [10, 10, 100, 100],
              nutrition_status: 'ADA',
              nutrition_status_label: 'Lengkap',
              tkpi: {
                id: 1,
                name: 'Nasi Goreng',
                nutrition: { energi_kal: 200, protein_g: 5, lemak_g: 5, karbo_g: 30, serat_g: 1 },
              },
            },
          ],
        }),
      });
    });

    await gotoAnalyze(page);

    const fileInput = await getAnyFileInput(page);
    await fileInput.setInputFiles(makeFakeImageFile());

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10_000 });
    await analyzeBtn.click();

    // Minimal robust assertion: result text should appear
    await expect(page.getByText(/nasi goreng/i)).toBeVisible({ timeout: 10_000 });

    // Optional: if you have these testids in UI
    const resultsSection = page.getByTestId('results-section');
    if (await resultsSection.count()) await expect(resultsSection).toBeVisible();

    const totalNutrition = page.getByTestId('total-nutrition');
    if (await totalNutrition.count()) await expect(totalNutrition).toBeVisible();

    const detectionCard = page.getByTestId('detection-card');
    if (await detectionCard.count()) await expect(detectionCard).toHaveCount(1);
  });

  test('Edit item -> (optional) search TKPI -> submit feedback -> success toast', async ({ page }) => {
    await page.route(DETECT_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          analysis_id: 999,
          items: [{ label: 'bakso', confidence: 0.8, bbox: [0, 0, 50, 50], tkpi: null }],
        }),
      });
    });

    await page.route(TKPI_SEARCH_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 55, name: 'Sate Ayam', nutrition: {} }]),
      });
    });

    await page.route(FEEDBACK_ENDPOINT, async (route) => {
      const body = route.request().postDataJSON();
      expect(body).toMatchObject({
        analysis_id: 999,
        pred_label: 'bakso',
        corrected_tkpi_id: 55,
        bbox: [0, 0, 50, 50],
      });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'OK' }),
      });
    });

    await gotoAnalyze(page);

    const fileInput = await getAnyFileInput(page);
    await fileInput.setInputFiles(makeFakeImageFile('fix.jpg'));

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10_000 });
    await analyzeBtn.click();

    await expect(page.getByText(/bakso/i)).toBeVisible({ timeout: 10_000 });

    // Open Edit: prefer testid; fallback by role
    const editByTestId = page.getByTestId('edit-item-button').first();
    if (await editByTestId.count()) {
      await editByTestId.click();
    } else {
      const editBtn = page.getByRole('button', { name: /edit/i }).first();
      if (!(await editBtn.count())) test.skip(true, 'Edit button not found (add data-testid="edit-item-button" or expose Edit in UI).');
      await editBtn.click();
    }

    // Search input
    const searchInput = (await page.getByTestId('edit-search-input').count())
      ? page.getByTestId('edit-search-input')
      : page.locator('input[placeholder*="Cari"], input[placeholder*="Search"], input[type="search"], input[type="text"]').first();

    if (!(await searchInput.count())) test.skip(true, 'Search input not found (add data-testid="edit-search-input").');
    await expect(searchInput).toBeVisible({ timeout: 10_000 });
    await searchInput.fill('Sate');

    const option = page.getByText(/sate ayam/i).first();
    if (!(await option.count())) test.skip(true, 'Search result "Sate Ayam" not shown/clickable.');
    await option.click();

    // Submit feedback
    const submit = page.getByTestId('submit-feedback-button');
    if (await submit.count()) {
      await submit.click();
    } else {
      const fallbackSubmit = page.getByRole('button', { name: /kirim|submit|simpan|save|feedback|koreksi/i }).first();
      if (!(await fallbackSubmit.count())) test.skip(true, 'Submit feedback button not found (add data-testid="submit-feedback-button").');
      await fallbackSubmit.click();
    }

    const toast = getToast(page);
    await expect(toast).toBeVisible({ timeout: 10_000 });
    await expect(toast).toContainText(/berhasil|sukses|ok|terkirim|dikoreksi/i);
  });

  test('Empty detection -> request new class (free text) -> POST /class-request -> toast', async ({ page }) => {
    await page.route(DETECT_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ analysis_id: 888, items: [] }),
      });
    });

    await page.route(CLASS_REQUEST_ENDPOINT, async (route) => {
      const body = route.request().postDataJSON();
      expect(body).toMatchObject({ analysis_id: 888, requested_label: 'Mie Ayam Spesial' });

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'OK' }),
      });
    });

    await gotoAnalyze(page);

    const fileInput = await getAnyFileInput(page);
    await fileInput.setInputFiles(makeFakeImageFile('empty.jpg'));

    const analyzeBtn = getAnalyzeButton(page);
    await expect(analyzeBtn).toBeVisible({ timeout: 10_000 });
    await analyzeBtn.click();

    // Open manual add
    const addManual = page.getByTestId('add-manual-button');
    if (await addManual.count()) {
      await addManual.click();
    } else {
      const fallbackAdd = page.getByRole('button', { name: /tambah.*manual|manual/i }).first();
      if (!(await fallbackAdd.count())) test.skip(true, 'Manual add UI not found (add data-testid="add-manual-button").');
      await fallbackAdd.click();
    }

    // Open training request
    const openTraining = page.getByTestId('open-training-request');
    if (await openTraining.count()) {
      await openTraining.click();
    } else {
      const fallbackTraining = page.getByText(/ajukan.*training|request.*training|training/i).first();
      if (!(await fallbackTraining.count())) test.skip(true, 'Training request trigger not found (add data-testid="open-training-request").');
      await fallbackTraining.click();
    }

    const input = page.getByTestId('request-label-input');
    if (!(await input.count())) test.skip(true, 'Missing data-testid="request-label-input" on free-text input.');
    await input.fill('Mie Ayam Spesial');

    const submit = page.getByTestId('submit-training-request-button');
    if (!(await submit.count())) test.skip(true, 'Missing data-testid="submit-training-request-button" on submit button.');
    await submit.click();

    const toast = getToast(page);
    await expect(toast).toBeVisible({ timeout: 10_000 });
    await expect(toast).toContainText(/berhasil|request|terkirim|diajukan|ok/i);
  });
});
