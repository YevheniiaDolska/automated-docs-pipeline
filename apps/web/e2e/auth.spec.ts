import { test, expect } from "@playwright/test";
import {
  uniqueEmail,
  TEST_PASSWORD,
  registerAccount,
  login,
  getToken,
  clearAuth,
} from "./helpers";

test.describe("Registration", () => {
  test("registers a new user and redirects to onboarding", async ({ page }) => {
    const email = uniqueEmail();
    await page.goto("/register");

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel("Confirm password").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();

    // Should redirect to onboarding after successful registration + auto-login
    await page.waitForURL("**/onboarding", { timeout: 15_000 });

    // Token should be stored
    const token = await getToken(page);
    expect(token).toBeTruthy();
  });

  test("shows error for mismatched passwords", async ({ page }) => {
    await page.goto("/register");

    await page.getByLabel("Email").fill(uniqueEmail());
    await page.getByLabel("Password", { exact: true }).fill("password1");
    await page.getByLabel("Confirm password").fill("password2");
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(page.getByText("Passwords do not match")).toBeVisible();
  });

  test("shows error for duplicate email", async ({ page }) => {
    // Register first account
    const email = await registerAccount(page);

    // Clear auth and try to register with same email
    await clearAuth(page);
    await page.goto("/register");

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel("Confirm password").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Create account" }).click();

    // Should show an error about existing email
    await expect(
      page.getByText(/already exists|already registered|duplicate/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("has link to login page", async ({ page }) => {
    await page.goto("/register");
    const signInLink = page.getByText("Sign in");
    await expect(signInLink).toBeVisible();
    await expect(signInLink).toHaveAttribute("href", "/login");
  });
});

test.describe("Login", () => {
  let testEmail: string;

  test.beforeAll(async ({ browser }) => {
    // Create a test account to use for login tests
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    testEmail = await registerAccount(page);
    await ctx.close();
  });

  test("logs in and redirects to dashboard", async ({ page }) => {
    await login(page, testEmail);

    // Should be on dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Token should be stored
    const token = await getToken(page);
    expect(token).toBeTruthy();
  });

  test("shows error for invalid credentials", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(
      page.getByText(/invalid|incorrect|unauthorized/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("disables button while loading", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill(TEST_PASSWORD);

    // Slow down network to catch loading state
    await page.route("**/auth/login", async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.continue();
    });

    await page.getByRole("button", { name: "Sign in" }).click();

    // Button should be disabled with loading text
    await expect(
      page.getByRole("button", { name: /signing in/i }),
    ).toBeDisabled();
  });

  test("has link to register page", async ({ page }) => {
    await page.goto("/login");
    const signUpLink = page.getByText("Sign up");
    await expect(signUpLink).toBeVisible();
    await expect(signUpLink).toHaveAttribute("href", "/register");
  });
});

test.describe("Auth guard", () => {
  test("redirects unauthenticated users to login", async ({ page }) => {
    // Clear any existing auth
    await page.goto("/login");
    await clearAuth(page);

    // Try to access protected page
    await page.goto("/dashboard");

    // Should redirect to login
    await page.waitForURL("**/login", { timeout: 10_000 });
  });

  test("protected pages accessible after login", async ({ page }) => {
    // Register and get authenticated
    const email = await registerAccount(page);

    // Navigate to dashboard (skip onboarding for now)
    await page.goto("/dashboard");

    // Should stay on dashboard, not redirected to login
    await expect(page).toHaveURL(/\/dashboard/);
  });
});

test.describe("Logout", () => {
  test("clears token and redirects to login", async ({ page }) => {
    // Register and login
    await registerAccount(page);

    // Navigate to dashboard
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/);

    // Clear auth (simulates logout)
    await clearAuth(page);

    // Refresh should redirect to login since token is gone
    await page.reload();
    await page.waitForURL("**/login", { timeout: 10_000 });

    // Token should be gone
    const token = await getToken(page);
    expect(token).toBeFalsy();
  });
});
