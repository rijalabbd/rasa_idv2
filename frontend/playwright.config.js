import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Phase 0 E2E testing
 * Tests critical contract scenarios: success, empty, invalid schema, 422 error, timeout
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Run sequentially for better debugging
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for sequential execution
  reporter: 'list',
  
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], headless: true },
    },
  ],

  // Dev server not needed - we're using existing npm run dev
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: true,
  // },
});
