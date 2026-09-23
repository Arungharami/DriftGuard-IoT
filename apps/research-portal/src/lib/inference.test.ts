import { describe, it, expect, vi } from "vitest";
import { infer } from "./inference";
const env = { HF_INFERENCE_URL: "https://example.hf.space/predict", HF_TOKEN: "test", INFERENCE_API_KEY: "test", INFERENCE_FEATURES: '["x"]', RATE_LIMIT_URL: "https://example.upstash.io", RATE_LIMIT_TOKEN: "test" };
const input = { rows: [{ x: 1 }] };
describe("inference boundary", () => {
  it("fails closed without approved service configuration", async () => { expect((await infer(input, {})).status).toBe(503); });
  it("rejects invalid inputs and unapproved feature names", async () => {
    expect((await infer({ rows: [] }, env)).status).toBe(422);
    expect((await infer({ rows: [{ ip: "private" }] }, env)).status).toBe(422);
  });
  it("refuses arbitrary network destinations", async () => { expect((await infer(input, { ...env, HF_INFERENCE_URL: "http://localhost/predict" })).status).toBe(503); });
  it("enforces the distributed quota before contacting the model", async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json({ result: 31 }));
    expect((await infer(input, env, fetcher)).status).toBe(429); expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("does not expose upstream errors or synthetic predictions", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(Response.json({ result: 1 })).mockResolvedValueOnce(Response.json({ predictions: ["normal"], model_version: "a".repeat(16), synthetic_data: true, latency_seconds: 0.01 }));
    expect((await infer(input, env, fetcher)).status).toBe(503);
  });
  it("returns validated predictions and sends secrets only upstream", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(Response.json({ result: 1 })).mockResolvedValueOnce(Response.json({ predictions: ["normal"], model_version: "a".repeat(16), synthetic_data: false, latency_seconds: 0.01 }));
    const result = await infer(input, env, fetcher); expect(result.status).toBe(200);
    expect(JSON.stringify(result.body)).not.toContain("test");
  });
});
