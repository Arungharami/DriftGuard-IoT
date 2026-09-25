import { describe, it, expect, vi } from "vitest";
import recording from "@/data/stream-recording.json";
import { completionRate, readStream } from "./streaming";
const env = { DRIFTGUARD_STREAM_API_URL: "https://backend.example", DRIFTGUARD_DEMO_API_TOKEN: "server-only-test-token", NODE_ENV: "production" };
describe("read-only streaming boundary", () => {
  it("fails closed without credentials and on insecure URLs", async () => {
    const fetcher = vi.fn();
    expect(await readStream({}, fetcher)).toBeNull();
    for (const url of ["http://backend.example", "https://user:pass@backend.example", "https://backend.example?token=x"]) expect(await readStream({ ...env, DRIFTGUARD_STREAM_API_URL: url }, fetcher)).toBeNull();
    expect(fetcher).not.toHaveBeenCalled();
    fetcher.mockRejectedValue(new Error("redirect"));
    expect(await readStream(env, fetcher)).toBeNull();
  });
  it("uses server credentials and strips private fields", async () => {
    const fetcher = vi.fn(async (url: URL | RequestInfo, options?: RequestInit) => {
      expect(options?.headers).toEqual({ Authorization: "Bearer server-only-test-token" });
      expect(options?.redirect).toBe("error");
      expect(options?.cache).toBe("no-store");
      return Response.json(String(url).includes("/summary") ? { ...recording.summary, secret: "private", features: { raw: 1 } } : { events: [{ received_at_utc: recording.recorded_at_utc, status: "predicted", decision: "normal", evidence_tier: "synthetic_fixture", inference_ms: 1, reason: "private", event_id: "private" }] });
    });
    const result = await readStream(env, fetcher);
    expect(result?.events).toHaveLength(1);
    expect(JSON.stringify(result)).not.toContain("private");
    expect(completionRate(result!.summary)).toBeCloseTo(49.967, 2);
  });
  it("rejects invalid, oversized, unavailable and falsely reportable responses", async () => {
    for (const response of [Response.json({}, { status: 401 }), Response.json({ ...recording.summary, reportable: true }), new Response("x".repeat(65537)), Response.json({ ...recording.summary, inference_ms: { n: 1, p50: -1, p95: 0, p99: 0 } })]) {
      expect(await readStream(env, vi.fn(async () => response.clone()))).toBeNull();
    }
    expect(completionRate({ ...recording.summary, reportable: false, events_by_status: {}, first_prediction_utc: null })).toBeNull();
  });
});
