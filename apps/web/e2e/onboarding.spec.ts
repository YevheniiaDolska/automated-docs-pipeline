import { test, expect } from "@playwright/test";
import {
  registerAccount,
  completeOnboarding,
  uniqueEmail,
  TEST_PASSWORD,
} from "./helpers";

test.describe("Onboarding wizard", () => {
  test.beforeEach(async ({ page }) => {
    // Each test starts with a freshly registered user on /onboarding
    await registerAccount(page);
  });

  test("shows step 1 with progress bar", async ({ page }) => {
    await expect(page.getByText("Step 1 of 8")).toBeVisible();
    await expect(page.getByText("Project name")).toBeVisible();
    await expect(page.getByText("13%")).toBeVisible();
  });

  test("requires project name before proceeding", async ({ page }) => {
    // Continue button should be disabled when project name is empty
    const continueBtn = page.getByRole("button", { name: "Continue" });
    await expect(continueBtn).toBeDisabled();

    // Fill in project name
    await page.locator('input[type="text"]').fill("Test Project");
    await expect(continueBtn).toBeEnabled();
  });

  test("navigates forward and backward through all steps", async ({
    page,
  }) => {
    // Step 1 -> 2
    await page.locator('input[type="text"]').fill("Test Project");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByText("Step 2 of 8")).toBeVisible();
    await expect(page.getByText("Project type")).toBeVisible();

    // Step 2 -> 3
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByText("Step 3 of 8")).toBeVisible();
    await expect(page.getByText("Documentation scope")).toBeVisible();

    // Back to step 2
    await page.getByRole("button", { name: "Back" }).click();
    await expect(page.getByText("Step 2 of 8")).toBeVisible();

    // Back to step 1
    await page.getByRole("button", { name: "Back" }).click();
    await expect(page.getByText("Step 1 of 8")).toBeVisible();

    // Back button should be disabled on step 1
    await expect(page.getByRole("button", { name: "Back" })).toBeDisabled();
  });

  test("shows all project types on step 2", async ({ page }) => {
    await page.locator('input[type="text"]').fill("Test");
    await page.getByRole("button", { name: "Continue" }).click();

    const types = [
      "Web Application",
      "API Service",
      "Library / SDK",
      "CLI Tool",
      "Mobile App",
      "Other",
    ];
    for (const t of types) {
      await expect(page.getByText(t)).toBeVisible();
    }
  });

  test("shows documentation scope options on step 3", async ({ page }) => {
    // Navigate to step 3
    await page.locator('input[type="text"]').fill("Test");
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByText("None")).toBeVisible();
    await expect(page.getByText("Basic")).toBeVisible();
    await expect(page.getByText("Standard")).toBeVisible();
    await expect(page.getByText("Full")).toBeVisible();
  });

  test("shows API protocol checkboxes on step 6", async ({ page }) => {
    // Navigate to step 6
    await page.locator('input[type="text"]').fill("Test");
    for (let i = 0; i < 5; i++) {
      await page.getByRole("button", { name: "Continue" }).click();
    }

    await expect(page.getByText("API protocols")).toBeVisible();
    await expect(page.getByText("REST (OpenAPI)")).toBeVisible();
    await expect(page.getByText("GraphQL")).toBeVisible();
    await expect(page.getByText("gRPC (Protobuf)")).toBeVisible();
    await expect(page.getByText("AsyncAPI (event-driven)")).toBeVisible();
    await expect(page.getByText("WebSocket")).toBeVisible();
  });

  test("skips protocol step when doc need is none", async ({ page }) => {
    // Step 1: project name
    await page.locator('input[type="text"]').fill("Test");
    await page.getByRole("button", { name: "Continue" }).click();

    // Step 2: project type
    await page.getByRole("button", { name: "Continue" }).click();

    // Step 3: select "None" for documentation scope
    await page.getByText("None").click();
    await page.getByRole("button", { name: "Continue" }).click();

    // Step 4: repo URL
    await page.getByRole("button", { name: "Continue" }).click();

    // Step 5: team size
    await page.getByRole("button", { name: "Continue" }).click();

    // Should jump to step 7 (AI provider), skipping step 6 (protocols)
    await expect(page.getByText("Step 7 of 8")).toBeVisible();
    await expect(page.getByText("AI provider")).toBeVisible();
  });

  test("shows LLM providers on step 7", async ({ page }) => {
    // Navigate to step 7
    await page.locator('input[type="text"]').fill("Test");
    for (let i = 0; i < 6; i++) {
      await page.getByRole("button", { name: "Continue" }).click();
    }

    await expect(page.getByText("AI provider")).toBeVisible();
    await expect(page.getByText("Groq")).toBeVisible();
    await expect(page.getByText("DeepSeek")).toBeVisible();
    await expect(page.getByText("OpenAI")).toBeVisible();
  });

  test("shows integrations on step 8 with Algolia toggle", async ({
    page,
  }) => {
    // Navigate to step 8
    await page.locator('input[type="text"]').fill("Test");
    for (let i = 0; i < 7; i++) {
      await page.getByRole("button", { name: "Continue" }).click();
    }

    await expect(page.getByText("Integrations")).toBeVisible();
    await expect(page.getByText("Site generator")).toBeVisible();
    await expect(page.getByText("Enable Algolia search")).toBeVisible();

    // Algolia fields should be hidden initially
    await expect(page.getByText("Algolia App ID")).not.toBeVisible();

    // Toggle Algolia on
    await page.getByText("Enable Algolia search").click();

    // Algolia fields should appear
    await expect(page.getByText("Algolia App ID")).toBeVisible();
    await expect(page.getByText("Algolia Search API key")).toBeVisible();
    await expect(page.getByText("Algolia Index name")).toBeVisible();
  });

  test("step 8 shows Finish setup button instead of Continue", async ({
    page,
  }) => {
    // Navigate to step 8
    await page.locator('input[type="text"]').fill("Test");
    for (let i = 0; i < 7; i++) {
      await page.getByRole("button", { name: "Continue" }).click();
    }

    await expect(
      page.getByRole("button", { name: "Finish setup" }),
    ).toBeVisible();
    // Continue button should not exist on final step
    await expect(
      page.getByRole("button", { name: "Continue" }),
    ).not.toBeVisible();
  });

  test("completes full wizard and redirects to dashboard", async ({
    page,
  }) => {
    await completeOnboarding(page);

    // Should be on dashboard after successful onboarding
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("shows loading state on submit", async ({ page }) => {
    // Navigate to step 8
    await page.locator('input[type="text"]').fill("Test");
    for (let i = 0; i < 7; i++) {
      await page.getByRole("button", { name: "Continue" }).click();
    }

    // Slow down the API call to catch loading state
    await page.route("**/onboarding", async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.continue();
    });

    await page.getByRole("button", { name: "Finish setup" }).click();

    // Should show loading state
    await expect(
      page.getByRole("button", { name: "Setting up..." }),
    ).toBeDisabled();
  });
});
