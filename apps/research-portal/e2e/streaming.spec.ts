import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import recording from "../src/data/stream-recording.json";

test("offline recording is accessible, responsive and explicitly synthetic", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText("Backend offline · Recorded demonstration", { exact: true })).toBeVisible();
  await expect(page.getByText(/Recorded synthetic workstation demonstration/)).toBeVisible();
  await expect(page.getByText(/not a scientifically validated concept-drift detector/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()).violations).toEqual([]);
  const response = await page.request.get("/api/stream");
  expect(response.status()).toBe(503);
  expect(response.headers()["cache-control"]).toContain("no-store");
});

test("loading, live, stale and failure states do not mislabel evidence", async ({ page }) => {
  let release: () => void = () => {};
  const pending = new Promise<void>((resolve) => { release = resolve; });
  let fail = false;
  await page.route("**/api/stream", async (route) => {
    await pending;
    if (fail) { await route.fulfill({ status: 502, body: "private backend error" }); return; }
    await route.fulfill({ json: { summary: recording.summary, events: [{ received_at_utc: recording.recorded_at_utc, status: "predicted", decision: "normal", evidence_tier: "synthetic_fixture", inference_ms: 1 }] } });
  });
  await page.goto("/demo");
  await expect(page.getByText("Connecting to streaming backend…", { exact: true })).toBeVisible();
  release();
  await expect(page.getByText("Streaming API connected", { exact: true })).toBeVisible();
  await expect(page.getByText("Idle or stale — no recent predictions", { exact: true })).toBeVisible();
  await expect(page.getByText(/predicted · normal · synthetic_fixture/)).toBeVisible();
  fail = true;
  await expect(page.getByText("Backend offline · Recorded demonstration", { exact: true })).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("private backend error")).toHaveCount(0);
});
