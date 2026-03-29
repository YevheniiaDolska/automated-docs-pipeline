import { test, expect } from "@playwright/test";
import {
  registerAccount,
  completeOnboarding,
  loginSmoke,
} from "./helpers";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    // Use smoke account or register + complete onboarding
    await loginSmoke(page);
  });

  test("shows welcome banner with user email", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Welcome back")).toBeVisible();
    // Email should appear somewhere in the welcome banner
    await expect(page.getByText("@")).toBeVisible();
  });

  test("shows pipeline dashboard heading", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Pipeline Dashboard")).toBeVisible();
  });

  test("shows usage overview section", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Usage overview")).toBeVisible();
    await expect(page.getByText("AI requests")).toBeVisible();
    await expect(page.getByText("Pages generated")).toBeVisible();
    await expect(page.getByText("API calls")).toBeVisible();
  });

  test("shows quality score section", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Quality score")).toBeVisible();
    // Either shows a score or "No runs yet"
    const ring = page.getByText(/Latest run|No runs yet/);
    await expect(ring).toBeVisible();
  });

  test("shows business chain status dots", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Payment")).toBeVisible();
    await expect(page.getByText("Plan active")).toBeVisible();
    await expect(page.getByText("Limits OK")).toBeVisible();
    await expect(page.getByText("Pipeline")).toBeVisible();
    await expect(page.getByText("Reports")).toBeVisible();
  });

  test("shows Run Pipeline button", async ({ page }) => {
    await page.goto("/dashboard");
    const btn = page.getByRole("button", { name: "Run Pipeline" });
    await expect(btn).toBeVisible();
    await expect(btn).toBeEnabled();
  });

  test("shows automation schedules section", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("Automation schedules")).toBeVisible();
  });

  test("Run Pipeline button shows loading state", async ({ page }) => {
    await page.goto("/dashboard");

    // Slow down the pipeline API call to catch loading state
    await page.route("**/pipeline/run", async (route) => {
      await new Promise((r) => setTimeout(r, 2000));
      await route.continue();
    });

    await page.getByRole("button", { name: "Run Pipeline" }).click();
    await expect(
      page.getByRole("button", { name: "Running..." }),
    ).toBeDisabled();
  });

  test("displays tier badge", async ({ page }) => {
    await page.goto("/dashboard");
    // TierBadge renders the tier name - should be visible somewhere
    await expect(
      page.getByText(/free|starter|pro|business|enterprise/i).first(),
    ).toBeVisible();
  });
});

test.describe("Dashboard auth guard", () => {
  test("redirects to login if not authenticated", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForURL("**/login", { timeout: 10_000 });
  });
});
