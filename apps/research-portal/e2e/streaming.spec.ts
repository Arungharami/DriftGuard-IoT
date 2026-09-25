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
    await route.fulfill({ json: { summary: { ...recording.summary, counters: { rejected_malformed: 3, rejected_schema: 2, duplicates_suppressed: 4 }, last_replay: { completed_at_utc: recording.recorded_at_utc, dataset_sha256: "a".repeat(64), sent: 500, target_rate_per_s: 50, achieved_rate_per_s: 49, evidence_tier: "synthetic_fixture" }, model_provenance: [{ model_sha256: recording.summary.model_sha256[0], dataset_sha256: "a".repeat(64), synthetic: true }] }, events: [{ received_at_utc: recording.recorded_at_utc, status: "predicted", decision: "normal", evidence_tier: "synthetic_fixture", inference_ms: 1 }] } });
  });
  await page.goto("/demo");
  await expect(page.getByText("Connecting to streaming backend…", { exact: true })).toBeVisible();
  release();
  await expect(page.getByText("Streaming API connected", { exact: true })).toBeVisible();
  await expect(page.getByText("Idle or stale — no recent predictions", { exact: true })).toBeVisible();
  await expect(page.getByText(/predicted · normal · synthetic_fixture/)).toBeVisible();
  await expect(page.getByText("Rejected: 5 · Dropped: 0", { exact: true })).toBeVisible();
  await expect(page.getByText("Duplicates: 4", { exact: true })).toBeVisible();
  await expect(page.getByText("49.00 / 50.00 events/s", { exact: true })).toBeVisible();
  await expect(page.getByText(/Model .*Dataset SHA-256:/)).toBeVisible();
  fail = true;
  await expect(page.getByText("Backend offline · Recorded demonstration", { exact: true })).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("private backend error")).toHaveCount(0);
});
