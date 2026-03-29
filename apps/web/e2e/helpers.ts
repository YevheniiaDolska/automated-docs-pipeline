import { type Page, expect } from "@playwright/test";

/**
 * Staging API base path. On staging.veri-doc.app, all API calls go through
 * /api/* prefix which Nginx strips before proxying to FastAPI.
 */
export const API_PREFIX = "/api";

/**
 * Generate a unique email for test isolation.
 * Uses timestamp + random suffix to avoid collisions across parallel runs.
 */
export function uniqueEmail(): string {
  const ts = Date.now();
  const rand = Math.random().toString(36).slice(2, 8);
  return `e2e-${ts}-${rand}@test.veri-doc.app`;
}

/** Default password used for all E2E test accounts. */
export const TEST_PASSWORD = "E2eTest!Secure#2026";

/**
 * Register a new account and return the email used.
 * After registration the user is automatically logged in and redirected to /onboarding.
 */
export async function registerAccount(
  page: Page,
  email?: string,
): Promise<string> {
  const testEmail = email ?? uniqueEmail();

  await page.goto("/register");
  await page.getByLabel("Email").fill(testEmail);
  await page.getByLabel("Password", { exact: true }).fill(TEST_PASSWORD);
  await page.getByLabel("Confirm password").fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();

  // Wait for redirect to onboarding (confirms successful registration + auto-login)
  await page.waitForURL("**/onboarding", { timeout: 15_000 });

  return testEmail;
}

/**
 * Log in with an existing account.
 * After login the user is redirected to /dashboard.
 */
export async function login(
  page: Page,
  email: string,
  password: string = TEST_PASSWORD,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();

  // Wait for redirect to dashboard
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
}

/**
 * Log in using the pre-existing smoke test account (env vars).
 * Falls back to creating a fresh account if smoke creds are not set.
 */
export async function loginSmoke(page: Page): Promise<string> {
  const email = process.env.E2E_SMOKE_EMAIL;
  const password = process.env.E2E_SMOKE_PASSWORD;

  if (email && password) {
    await login(page, email, password);
    return email;
  }

  // No smoke account configured -- register a fresh one and complete onboarding
  const freshEmail = await registerAccount(page);
  await completeOnboarding(page);
  return freshEmail;
}

/**
 * Complete the onboarding wizard with default values.
 * Assumes the user is already on /onboarding.
 *
 * Wizard steps:
 * 1. Project name (text input)
 * 2. Project type (radio: Web Application default)
 * 3. Documentation scope (radio: Standard default)
 * 4. Repository URL (text input, optional)
 * 5. Team size (radio: Just me default)
 * 6. API protocols (checkboxes, skipped if doc need = none)
 * 7. AI provider (radio: Groq default, + optional API key)
 * 8. Integrations (site generator select + Algolia toggle)
 */
export async function completeOnboarding(page: Page): Promise<void> {
  // Step 1: Project name (required)
  await expect(page.getByText("Project name")).toBeVisible();
  await page.locator('input[type="text"]').fill("E2E Test Project");
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 2: Project type -- Web Application is default, just click Continue
  await expect(page.getByText("Project type")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 3: Documentation scope -- Standard is default, just click Continue
  await expect(page.getByText("Documentation scope")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 4: Repository URL -- optional, skip
  await expect(page.getByText("Repository URL")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 5: Team size -- Just me is default, click Continue
  await expect(page.getByText("Team size")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 6: API protocols -- select REST
  await expect(page.getByText("API protocols")).toBeVisible();
  await page.getByText("REST (OpenAPI)").click();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 7: AI provider -- Groq is default, skip API key
  await expect(page.getByText("AI provider")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  // Step 8: Integrations -- defaults are fine, finish
  await expect(page.getByText("Integrations")).toBeVisible();
  await page.getByRole("button", { name: "Finish setup" }).click();

  // Wait for redirect to dashboard
  await page.waitForURL("**/dashboard", { timeout: 15_000 });
}

/**
 * Assert that the user is on an authenticated page (not redirected to login).
 */
export async function assertAuthenticated(page: Page): Promise<void> {
  // Should NOT be on login or register
  const url = page.url();
  expect(url).not.toContain("/login");
  expect(url).not.toContain("/register");
}

/**
 * Get the auth token from localStorage.
 */
export async function getToken(page: Page): Promise<string | null> {
  return page.evaluate(() => localStorage.getItem("veridoc_token"));
}

/**
 * Clear auth state (logout by removing token).
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => localStorage.removeItem("veridoc_token"));
}

/**
 * Wait for an API response matching a path pattern.
 */
export async function waitForApi(
  page: Page,
  pathPattern: string | RegExp,
): Promise<void> {
  await page.waitForResponse(
    (resp) => {
      const url = resp.url();
      if (typeof pathPattern === "string") {
        return url.includes(pathPattern) && resp.status() < 400;
      }
      return pathPattern.test(url) && resp.status() < 400;
    },
    { timeout: 15_000 },
  );
}
