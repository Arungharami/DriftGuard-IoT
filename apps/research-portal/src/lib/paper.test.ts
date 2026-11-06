import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { batteryLife, parsePaper, slugify, tokenizeInline } from "./paper";

describe("parsePaper", () => {
  const paper = parsePaper(readFileSync(join(process.cwd(), "src/content/paper.md"), "utf8"));

  it("reads the title, authors and all required sections", () => {
    expect(paper.title).toMatch(/^DriftGuard-IoT/);
    expect(paper.authors).toContain("Florida Atlantic University");
    expect(paper.sections.map((s) => s.id)).toEqual([
      "abstract",
      "introduction",
      "literature-survey",
      "system-model",
      "proposed-method",
      "simulation-set-up",
      "results-and-discussion",
      "limitations-and-threats-to-validity",
      "summary-and-conclusions",
      "references",
    ]);
  });

  it("stays inside the 4,000-6,000 word guideline and keeps every figure and reference", () => {
    expect(paper.wordCount).toBeGreaterThanOrEqual(4000);
    expect(paper.wordCount).toBeLessThanOrEqual(6000);
    const blocks = paper.sections.flatMap((s) => s.blocks);
    expect(blocks.filter((b) => b.type === "figure")).toHaveLength(6);
    expect(blocks.filter((b) => b.type === "table")).toHaveLength(4);
    expect(blocks.filter((b) => b.type === "reference")).toHaveLength(22);
  });

  it("parses lists, tables and maths from a small source", () => {
    const p = parsePaper(
      "# T\n\nA\n\n## I. Intro\n\n1. **One.** x\n2. two\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n```latex\nx^2\n```\n\n*Table I. cap*\n",
    );
    const b = p.sections[0]?.blocks ?? [];
    expect(b[1]).toEqual({ type: "list", ordered: true, items: ["**One.** x", "two"] });
    expect(b[2]).toEqual({ type: "table", head: ["a", "b"], rows: [["1", "2"]] });
    expect(b[3]).toEqual({ type: "math", tex: "x^2", n: 1 });
    expect(b[4]).toEqual({ type: "caption", text: "Table I. cap" });
  });
});

describe("helpers", () => {
  it("slugifies roman-numbered and lettered headings", () => {
    expect(slugify("VI. Results and Discussion")).toBe("results-and-discussion");
    expect(slugify("B. Comparison of adaptation policies")).toBe("comparison-of-adaptation-policies");
  });

  it("tokenizes citations, emphasis and links", () => {
    expect(tokenizeInline("see [13], *IEEE* and **x** at https://doi.org/1.")).toEqual([
      { kind: "text", value: "see " },
      { kind: "cite", n: 13 },
      { kind: "text", value: ", " },
      { kind: "italic", value: "IEEE" },
      { kind: "text", value: " and " },
      { kind: "bold", value: "x" },
      { kind: "text", value: " at " },
      { kind: "link", value: "https://doi.org/1", href: "https://doi.org/1" },
      { kind: "text", value: "." },
    ]);
  });

  it("reproduces the paper's battery-life figures", () => {
    const minute = batteryLife({ periodS: 60, activeS: 2 });
    expect(minute.avgMa).toBeCloseTo(4.08, 2);
    expect(minute.days).toBeCloseTo(21.2, 1);
    expect(batteryLife({ periodS: 300, activeS: 2 }).days).toBeCloseTo(102.9, 0);
  });
});
