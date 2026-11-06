import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("navigation, evidence filtering and empty research charts", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/experiments");
  await expect(page.getByRole("heading", { name: "Experiments", exact: true })).toBeVisible();
  await page.getByLabel("Experiment area", { exact: true }).selectOption("unknown");
  await expect(page.getByRole("heading", { name: "Unknown-attack recognition · Blocked" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Cross-dataset generalization · Blocked" })).toHaveCount(0);
  await page.getByLabel("Filter verified results by dataset").selectOption("all");
  await expect(page.getByText("No verified results match this selection.", { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()).violations).toEqual([]);
  expect(errors).toEqual([]);
});

test("all academic pages load and dataset descriptions retain provenance", async ({ page }) => {
  for (const route of ["/", "/paper", "/research", "/reference-paper", "/contribution", "/architecture", "/datasets", "/model-explorer", "/cross-domain", "/drift-lab", "/explainability", "/robustness", "/resources", "/reproducibility", "/publications", "/team"]) {
    const response = await page.goto(route); expect(response?.status()).toBe(200);
    await expect(page.locator("h1")).toHaveCount(1);
  }
  await page.goto("/datasets");
  await expect(page.getByText("Edge-IIoTset", { exact: true }).first()).toBeVisible();
});

test("model demo handles unavailable service and invalid JSON accessibly", async ({ page }) => {
  await page.goto("/demo");
  await page.getByRole("button", { name: "Check model service" }).click();
  await expect(page.getByRole("status").filter({ hasText: /No approved research model|Check JSON formatting/ })).toContainText("No approved research model");
  await page.getByLabel("Feature rows (JSON)").fill("not-json");
  await page.getByRole("button", { name: "Check model service" }).click();
  await expect(page.getByRole("status").filter({ hasText: /No approved research model|Check JSON formatting/ })).toContainText("Check JSON formatting");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()).violations).toEqual([]);
});

test("paper switches between modern and classic views without layout overflow", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/paper");
  await expect(page.locator("h1")).toContainText("DriftGuard-IoT");
  await expect(page.getByRole("button", { name: /Modern/ })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Sensor-node battery-life calculator")).toBeVisible();
  await page.getByRole("button", { name: /Classic paper/ }).click();
  await expect(page.getByRole("button", { name: /Classic paper/ })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Sensor-node battery-life calculator")).toBeHidden();
  await expect(page.getByRole("img", { name: /Grouped bar chart of post-drift macro-F1/ })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: /Classic paper/ })).toHaveAttribute("aria-pressed", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()).violations).toEqual([]);
  expect(errors).toEqual([]);
});
