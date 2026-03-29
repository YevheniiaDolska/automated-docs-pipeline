import { test, expect } from "@playwright/test";
import { loginSmoke } from "./helpers";

test.describe("Settings page", () => {
  test.beforeEach(async ({ page }) => {
    await loginSmoke(page);
    await page.goto("/settings");
  });

  test("shows settings heading", async ({ page }) => {
    await expect(page.getByText("Pipeline Settings")).toBeVisible();
    await expect(
      page.getByText(
        "Configure which pipeline modules run and how the pipeline behaves.",
      ),
    ).toBeVisible();
  });

  test("shows flow mode options", async ({ page }) => {
    await expect(page.getByText("Flow mode")).toBeVisible();
    await expect(page.getByText("Hybrid")).toBeVisible();
    await expect(page.getByText("API-first")).toBeVisible();
    await expect(page.getByText("Code-first")).toBeVisible();
  });

  test("shows flow mode descriptions", async ({ page }) => {
    await expect(
      page.getByText("API-first + code-first combined"),
    ).toBeVisible();
    await expect(
      page.getByText("OpenAPI spec is source of truth"),
    ).toBeVisible();
    await expect(
      page.getByText("Source code is source of truth"),
    ).toBeVisible();
  });

  test("shows default protocols checkboxes", async ({ page }) => {
    await expect(page.getByText("Default protocols")).toBeVisible();
    await expect(page.getByText("REST (OpenAPI)")).toBeVisible();
    await expect(page.getByText("GraphQL")).toBeVisible();
    await expect(page.getByText("gRPC")).toBeVisible();
    await expect(page.getByText("AsyncAPI")).toBeVisible();
    await expect(page.getByText("WebSocket")).toBeVisible();
  });

  test("shows sandbox backend selector", async ({ page }) => {
    await expect(page.getByText("Sandbox backend")).toBeVisible();
    const select = page.locator("select").first();
    await expect(select).toBeVisible();
  });

  test("shows Algolia toggle", async ({ page }) => {
    await expect(
      page.getByText("Algolia search integration"),
    ).toBeVisible();
  });

  test("shows pipeline modules section", async ({ page }) => {
    await expect(page.getByText("Pipeline modules")).toBeVisible();
    await expect(
      page.getByText("Toggle individual pipeline phases"),
    ).toBeVisible();
  });

  test("shows module tier groups", async ({ page }) => {
    // At least one tier group header should be visible
    const tierHeaders = page.getByText(/Starter tier|Pro tier|Business tier|Enterprise tier/);
    await expect(tierHeaders.first()).toBeVisible({ timeout: 10_000 });
  });

  test("locked modules show upgrade message", async ({ page }) => {
    // If user is on free/starter, some modules should show "Requires X"
    const requiresLabel = page.getByText(/Requires (Pro|Business|Enterprise)/);
    const count = await requiresLabel.count();
    // On a free account, there should be locked modules
    expect(count).toBeGreaterThan(0);
  });

  test("can change flow mode", async ({ page }) => {
    // Click API-first radio
    const apiFirstRadio = page.locator('input[type="radio"][value="api-first"]');
    await apiFirstRadio.click();

    // Should show success message
    await expect(page.getByText("Settings saved.")).toBeVisible({
      timeout: 10_000,
    });

    // Switch back to hybrid
    const hybridRadio = page.locator('input[type="radio"][value="hybrid"]');
    await hybridRadio.click();
    await expect(page.getByText("Settings saved.")).toBeVisible({
      timeout: 10_000,
    });
  });

  test("shows referral section", async ({ page }) => {
    await expect(
      page.getByText("Badge and referral income"),
    ).toBeVisible();
    await expect(
      page.getByText("Read referral terms and recurring payout rules"),
    ).toBeVisible();
  });

  test("shows referral details", async ({ page }) => {
    await expect(page.getByText("Referral code:")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText("Referral link:")).toBeVisible();
    await expect(page.getByText("Accrued:")).toBeVisible();
  });

  test("shows payout settings", async ({ page }) => {
    await expect(page.getByText("Payout settings")).toBeVisible({
      timeout: 15_000,
    });
    await expect(
      page.getByRole("button", { name: "Save payout settings" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Run payout queue" }),
    ).toBeVisible();
  });
});

test.describe("Settings auth guard", () => {
  test("redirects to login if not authenticated", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForURL("**/login", { timeout: 10_000 });
  });
});
