import type { Metadata } from "next";

import { Card, PageHeader, Section } from "@/components/ui";
import { REPO_URL } from "@/content/site";

export const metadata: Metadata = { title: "Reproducibility" };

const RULES = [
  "Train/test separation happens before fitting any encoder, scaler, selector or resampler.",
  "Test partitions are never used for fitting, tuning, threshold selection or model updates.",
  "Chronological simulations never read data later than the current simulation time.",
  "Every run writes a manifest: config hash, seed, source fingerprints, software versions, git commit.",
  "Only manifests of kind “research” may feed published results; smoke and synthetic runs cannot.",
  "Figures are produced only from verified experiment artifacts.",
];

export default function ReproducibilityPage() {
  return (
    <>
      <PageHeader
        title="Reproducibility"
        lede="How any number on this site can be traced back to code, configuration, data and environment."
      />
      <Section title="Protocol rules">
        <ul className="list-disc space-y-1 pl-6 text-ink-muted">
          {RULES.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      </Section>
      <Section title="Run it yourself">
        <Card title="Synthetic smoke run (no datasets needed)">
          <pre className="overflow-x-auto rounded bg-surface-muted p-3 font-mono text-xs text-ink">
            {`pip install -e ".[dev]" -c requirements/constraints-py311.txt
driftguard smoke`}
          </pre>
          <p>
            The smoke run validates the pipeline only. Its output is labelled as synthetic and is
            not a research result.{" "}
            <a className="underline" href={REPO_URL}>
              Repository
            </a>
          </p>
        </Card>
      </Section>
    </>
  );
}
