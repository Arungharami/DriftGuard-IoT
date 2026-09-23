import { z } from "zod";

export const requestSchema = z.object({
  rows: z.array(z.record(z.string().regex(/^[A-Za-z0-9_.-]{1,64}$/), z.union([
    z.number().finite(), z.string().max(64),
  ]))).min(1).max(16),
}).strict();
const responseSchema = z.object({
  predictions: z.array(z.string().max(64)).min(1).max(16),
  model_version: z.string().regex(/^[a-f0-9]{16}$/),
  synthetic_data: z.literal(false),
  latency_seconds: z.number().finite().nonnegative(),
}).strict();

export async function infer(body: unknown, env: Record<string, string | undefined>, fetcher: typeof fetch = fetch) {
  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) return { status: 422, body: { error: "Enter 1–16 rows of valid feature values." } };
  const unavailable = { status: 503, body: { error: "No approved research model is available. Please check the evidence page." } };
  const { HF_INFERENCE_URL, HF_TOKEN, INFERENCE_API_KEY, INFERENCE_FEATURES, RATE_LIMIT_URL, RATE_LIMIT_TOKEN } = env;
  if (!HF_INFERENCE_URL || !HF_TOKEN || !INFERENCE_API_KEY || !INFERENCE_FEATURES || !RATE_LIMIT_URL || !RATE_LIMIT_TOKEN) return unavailable;
  try {
    const endpoint = new URL(HF_INFERENCE_URL);
    const limiter = new URL(RATE_LIMIT_URL);
    if (endpoint.protocol !== "https:" || !endpoint.hostname.endsWith(".hf.space") || endpoint.pathname !== "/predict" || endpoint.username || endpoint.password || endpoint.search || endpoint.port) return unavailable;
    if (limiter.protocol !== "https:" || !limiter.hostname.endsWith(".upstash.io") || limiter.username || limiter.password || limiter.port) return unavailable;
    const features = z.array(z.string().min(1)).min(1).max(128).parse(JSON.parse(INFERENCE_FEATURES));
    if (parsed.data.rows.some((row) => Object.keys(row).length !== features.length || features.some((name) => !(name in row)))) return { status: 422, body: { error: "Feature names do not match the approved model." } };
    // Global atomic quota works across serverless replicas; no IP addresses are retained.
    const quotaResponse = await fetcher(limiter, {
      method: "POST", headers: { Authorization: `Bearer ${RATE_LIMIT_TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify(["EVAL", "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],120) end; return n", "1", `driftguard:inference:${Math.floor(Date.now() / 60000)}`]),
      signal: AbortSignal.timeout(3000), redirect: "error", cache: "no-store",
    });
    if (!quotaResponse.ok) return unavailable;
    const quota = z.object({ result: z.number().int().positive() }).parse(await quotaResponse.json());
    if (quota.result > 30) return { status: 429, body: { error: "The demo request limit has been reached. Retry in one minute." } };
    const response = await fetcher(endpoint, {
      method: "POST", headers: { Authorization: `Bearer ${HF_TOKEN}`, "X-Inference-Key": INFERENCE_API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify(parsed.data), signal: AbortSignal.timeout(10000), redirect: "error", cache: "no-store",
    });
    if (!response.ok) return unavailable;
    const result = responseSchema.parse(await response.json());
    if (result.predictions.length !== parsed.data.rows.length) return unavailable;
    return { status: 200, body: result };
  } catch { return unavailable; }
}
