import { describe, expect, it } from "vitest";

import rawCatalog from "@/data/datasets.json";

import { catalog, catalogSchema } from "./datasets";

describe("dataset catalog", () => {
  it("lists the three study datasets", () => {
    expect(catalog.datasets.map((d) => d.id).sort()).toEqual([
      "edge_iiotset",
      "ton_iot",
      "wustl_iiot_2021",
    ]);
  });

  it("never claims artifact redistribution is permitted before review", () => {
    for (const d of catalog.datasets) {
      expect(d.license.derived_artifact_redistribution).not.toBe("permitted");
    }
  });

  it("rejects entries with an unknown license status", () => {
    const bad = structuredClone(rawCatalog) as { datasets: { license: { academic_use: string } }[] };
    bad.datasets[0]!.license.academic_use = "probably fine";
    expect(() => catalogSchema.parse(bad)).toThrow();
  });
});
