import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("homepage workflow supports playback, manual stages and reduced motion", async ({ page }) => {
  await page.goto("/");
  const workflow = page.getByRole("region", { name: "How DriftGuard-IoT works" });
  await expect(workflow).toBeVisible();
  await workflow.getByRole("button", { name: "Play animation", exact: true }).click();
  await expect(workflow.getByRole("button", { name: "Pause animation", exact: true })).toBeVisible();
  await workflow.getByRole("button", { name: /Drift monitoring/ }).click();
  await expect(page.locator("#workflow-caption")).toContainText("A drift alert alone does not prove an attack");
  await expect(workflow.getByRole("button", { name: "Play animation", exact: true })).toBeVisible();
  await workflow.getByRole("button", { name: "Next stage", exact: true }).click();
  await expect(page.locator("#workflow-caption")).toContainText("Digital dashboard");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(workflow.getByRole("button", { name: "Play animation", exact: true })).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).include("#how-it-works").withTags(["wcag2a", "wcag2aa"]).analyze()).violations).toEqual([]);
});
