// playwright.config.js (root)
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './frontend/e2e',
  timeout: 60_000,
  use: {
    headless: true,
    baseURL: 'http://localhost:5173',
  },
  reporter: [['list']],
});
