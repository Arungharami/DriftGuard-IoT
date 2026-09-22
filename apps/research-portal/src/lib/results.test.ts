import { describe, expect, it } from "vitest";

import { parseResultsIndex, resultsIndex } from "./results";

const hex = (n: number) => "a".repeat(n);

const validEntry = {
  id: "ton_iot-dt-holdout",
  experiment: "baseline",
  dataset: "ton_iot",
  model: "decision_tree",
  evaluation: "stratified_holdout",
  metrics: { macro_f1: 0.5 },
  provenance: {
    run_id: "run-1",
    kind: "research",
    synthetic_data: false,
    config_hash: hex(64),
    git_commit: hex(40),
    data_fingerprints: { ton_iot: hex(64) },
  },
};

const index = (results: unknown[]) => ({ schema_version: 1, generated_at: null, results });

describe("results contract", () => {
  it("ships with no results until verified research runs exist", () => {
    expect(resultsIndex.results).toEqual([]);
  });

  it("accepts a fully provenanced research entry", () => {
    expect(parseResultsIndex(index([validEntry])).results).toHaveLength(1);
  });

  it.each([
    ["smoke runs", { ...validEntry.provenance, kind: "smoke" }],
    ["synthetic data", { ...validEntry.provenance, synthetic_data: true }],
    ["missing config hash", { ...validEntry.provenance, config_hash: "" }],
    ["missing git commit", { ...validEntry.provenance, git_commit: "HEAD" }],
  ])("rejects %s", (_label, provenance) => {
    expect(() => parseResultsIndex(index([{ ...validEntry, provenance }]))).toThrow();
  });

  it("rejects non-finite metrics", () => {
    const entry = { ...validEntry, metrics: { macro_f1: Number.NaN } };
    expect(() => parseResultsIndex(index([entry]))).toThrow();
  });
});
