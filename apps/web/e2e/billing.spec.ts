import { test, expect } from "@playwright/test";
import { loginSmoke } from "./helpers";

test.describe("Billing page", () => {
  test.beforeEach(async ({ page }) => {
    await loginSmoke(page);
    await page.goto("/billing");
  });

  test("shows billing heading", async ({ page }) => {
    await expect(page.getByText("Billing")).toBeVisible();
    await expect(
      page.getByText("Manage your subscription, usage, and invoices."),
    ).toBeVisible();
  });

  test("shows current plan section with tier badge", async ({ page }) => {
    await expect(page.getByText("Current plan")).toBeVisible();
    // Tier badge should be visible
    await expect(
      page.getByText(/free|starter|pro|business|enterprise/i).first(),
    ).toBeVisible();
  });

  test("shows usage meters", async ({ page }) => {
    await expect(page.getByText("Usage this period")).toBeVisible();
    await expect(page.getByText("AI requests")).toBeVisible();
    await expect(page.getByText("Pages generated")).toBeVisible();
    await expect(page.getByText("API calls")).toBeVisible();
  });

  test("shows business chain status", async ({ page }) => {
    await expect(page.getByText("Business chain")).toBeVisible();
    await expect(page.getByText("Payment")).toBeVisible();
    await expect(page.getByText("Plan active")).toBeVisible();
    await expect(page.getByText("Limits applied")).toBeVisible();
    await expect(page.getByText("Pipeline access")).toBeVisible();
    await expect(page.getByText("Reports ready")).toBeVisible();
  });

  test("shows available plans section", async ({ page }) => {
    await expect(page.getByText("Available plans")).toBeVisible({
      timeout: 15_000,
    });
  });

  test("highlights current plan in plan grid", async ({ page }) => {
    await expect(page.getByText("Available plans")).toBeVisible({
      timeout: 15_000,
    });
    // The current plan card should have a "Current" label
    await expect(page.getByText("Current")).toBeVisible();
  });

  test("shows upgrade buttons for non-current plans", async ({ page }) => {
    await expect(page.getByText("Available plans")).toBeVisible({
      timeout: 15_000,
    });
    // At least one Upgrade button should exist (user is on free tier)
    const upgradeButtons = page.getByRole("button", { name: "Upgrade" });
    const count = await upgradeButtons.count();
    expect(count).toBeGreaterThan(0);
  });

  test("shows enterprise contact section", async ({ page }) => {
    await expect(
      page.getByText("Need enterprise pricing?"),
    ).toBeVisible();
    await expect(page.getByText("Book a call")).toBeVisible();
    await expect(page.getByText("Referral program")).toBeVisible();
  });

  test("shows renewal info or trial status", async ({ page }) => {
    // Either shows "Renews in X days" or "Trial ends" depending on status
    await expect(page.getByText("Current plan")).toBeVisible();
    const renewalOrTrial = page.getByText(/Renews in|Trial ends/);
    await expect(renewalOrTrial).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Billing auth guard", () => {
  test("redirects to login if not authenticated", async ({ page }) => {
    await page.goto("/billing");
    await page.waitForURL("**/login", { timeout: 10_000 });
  });
});
