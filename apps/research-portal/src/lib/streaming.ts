import { z } from "zod";

const count = z.number().int().nonnegative();
const label = z.string().regex(/^[A-Za-z0-9_. -]{1,64}$/);
const counts = z.record(label, count);
const percentiles = z.object({ n: count, p50: z.number().finite().nonnegative().nullable(), p95: z.number().finite().nonnegative().nullable(), p99: z.number().finite().nonnegative().nullable() });
export const summarySchema = z.object({
  events_by_status: counts, predictions_by_decision: counts, events_by_evidence_tier: counts,
  counters: counts, inference_ms: percentiles, end_to_end_ms: percentiles,
  first_prediction_utc: z.iso.datetime({ offset: true }).nullable(),
  last_prediction_utc: z.iso.datetime({ offset: true }).nullable(),
  monitor_alarms: count, model_sha256: z.array(z.string().regex(/^[a-f0-9]{64}$/)).max(100),
  reportable: z.literal(false),
});
const eventSchema = z.object({
  received_at_utc: z.iso.datetime({ offset: true }),
  status: z.enum(["predicted", "rejected", "duplicate", "model_unavailable"]),
  decision: label.nullable(),
  evidence_tier: z.enum(["synthetic_fixture", "dataset_replay", "lab_capture"]).nullable(),
  inference_ms: z.number().finite().nonnegative().nullable(),
});
export const snapshotSchema = z.object({ summary: summarySchema, events: z.array(eventSchema).max(50) });
export type Snapshot = z.infer<typeof snapshotSchema>;

/** Fixed server-owned destination; never accept a URL or token from the browser. */
export async function readStream(env: Record<string, string | undefined>, fetcher: typeof fetch = fetch): Promise<Snapshot | null> {
  if (!env.DRIFTGUARD_STREAM_API_URL || !env.DRIFTGUARD_DEMO_API_TOKEN) return null;
  try {
    const base = new URL(env.DRIFTGUARD_STREAM_API_URL);
    const local = env.NODE_ENV !== "production" && ["127.0.0.1", "localhost", "[::1]"].includes(base.hostname);
    if ((base.protocol !== "https:" && !(local && base.protocol === "http:")) || base.username || base.password || base.search || base.hash || base.pathname !== "/") return null;
    const read = async (path: string) => {
      const response = await fetcher(new URL(path, base), {
        headers: { Authorization: `Bearer ${env.DRIFTGUARD_DEMO_API_TOKEN}` },
        cache: "no-store", redirect: "error", signal: AbortSignal.timeout(4000),
      });
      if (!response.ok) throw new Error("stream unavailable");
      // Bound decoded bytes even when Content-Length is absent or dishonest.
      const reader = response.body?.getReader();
      if (!reader) throw new Error("empty response");
      const chunks: Uint8Array[] = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > 65536) throw new Error("oversized response");
          chunks.push(value);
        }
      } finally { void reader.cancel().catch(() => {}); }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
      return JSON.parse(new TextDecoder().decode(bytes));
    };
    const [summary, recent] = await Promise.all([read("/v1/summary"), read("/v1/events/recent?limit=20")]);
    // Zod strips unapproved fields, including any accidental features, URLs or identifiers.
    return snapshotSchema.parse({ summary, events: recent.events });
  } catch { return null; }
}

/** Retained-window completion rate, not producer rate or an edge-device benchmark. */
export function completionRate(summary: Snapshot["summary"]): number | null {
  const n = summary.events_by_status.predicted ?? 0;
  if (n < 2 || !summary.first_prediction_utc || !summary.last_prediction_utc) return null;
  const seconds = (Date.parse(summary.last_prediction_utc) - Date.parse(summary.first_prediction_utc)) / 1000;
  return seconds > 0 ? (n - 1) / seconds : null;
}
