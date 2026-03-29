import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for VeriDoc web application.
 *
 * Tests run against the STAGING server (staging.veri-doc.app).
 * No local dev server is started -- the staging deployment is used directly.
 *
 * Usage:
 *   npx playwright test                    - run all tests headless (Chromium only)
 *   npx playwright test --project=firefox  - run on Firefox
 *   npx playwright test --ui               - interactive UI mode
 *   npx playwright test e2e/auth.spec.ts   - run one file
 *   npx playwright test --headed           - run with browser visible
 *
 * Environment variables:
 *   E2E_BASE_URL       - override base URL (default: https://staging.veri-doc.app)
 *   E2E_SMOKE_EMAIL    - pre-existing test account email
 *   E2E_SMOKE_PASSWORD - pre-existing test account password
 *   CI                 - set to any value in CI for strict mode
 */

const BASE_URL = process.env.E2E_BASE_URL ?? "https://staging.veri-doc.app";

export default defineConfig({
  testDir: "./e2e",

  // Auth flow tests must run sequentially; others can run in parallel
  fullyParallel: false,

  // Fail the build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Serial on CI; parallel locally
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "playwright-report/results.json" }],
  ],

  use: {
    baseURL: BASE_URL,

    // Collect trace on first retry to diagnose failures
    trace: "on-first-retry",

    // Screenshot on failure only
    screenshot: "only-on-failure",

    // Keep video on failure
    video: "retain-on-failure",

    // Timeout for each action (click, fill, etc.)
    actionTimeout: 15_000,

    // Timeout for navigation (staging can be slower than local)
    navigationTimeout: 30_000,

    // Extra HTTP headers for staging identification
    extraHTTPHeaders: {
      "X-Test-Suite": "playwright-e2e",
    },
  },

  // Global test timeout (generous for staging network latency)
  timeout: 90_000,

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
  ],

  // No webServer block -- tests hit the live staging deployment
});
