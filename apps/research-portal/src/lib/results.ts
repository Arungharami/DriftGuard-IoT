/**
 * Versioned research-results contract.
 *
 * The portal renders metrics ONLY from `src/data/results/index.json`, validated here at
 * build time. Every entry must reference a `kind: "research"` run manifest; smoke or
 * development runs and synthetic data are rejected, so they can never be displayed as
 * research results. Simulated demonstrations use a separate, visibly labelled path.
 */
import { z } from "zod";

import rawIndex from "@/data/results/index.json";

export const RESULTS_SCHEMA_VERSION = 1;

const metricValue = z.number().finite();

export const resultEntrySchema = z.object({
  id: z.string().min(1),
  experiment: z.string().min(1),
  dataset: z.string().min(1),
  model: z.string().min(1),
  evaluation: z.enum(["stratified_holdout", "chronological", "cross_dataset", "rolling_origin"]),
  metrics: z.record(z.string(), metricValue),
  confidence_intervals: z
    .record(z.string(), z.object({ low: metricValue, high: metricValue, level: z.number() }))
    .optional(),
  provenance: z.object({
    manifest_url: z.string().regex(/^\/manifests\/[a-f0-9]{64}\.json$/).optional(),
    manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/).optional(),
    run_id: z.string().min(1),
    kind: z.literal("research"),
    synthetic_data: z.literal(false),
    config_hash: z.string().regex(/^[0-9a-f]{64}$/),
    git_commit: z.string().regex(/^[0-9a-f]{40}$/),
    data_fingerprints: z.record(z.string(), z.string().regex(/^[0-9a-f]{64}$/)),
  }),
});

export const resultsIndexSchema = z.object({
  schema_version: z.literal(RESULTS_SCHEMA_VERSION),
  generated_at: z.string().nullable(),
  results: z.array(resultEntrySchema),
});

export type ResultEntry = z.infer<typeof resultEntrySchema>;
export type ResultsIndex = z.infer<typeof resultsIndexSchema>;

export function parseResultsIndex(data: unknown): ResultsIndex {
  return resultsIndexSchema.parse(data);
}

/** Parsed at module load, so an invalid index fails `next build`. */
export const resultsIndex: ResultsIndex = parseResultsIndex(rawIndex);
