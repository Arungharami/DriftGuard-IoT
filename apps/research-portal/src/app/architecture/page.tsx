import type { Metadata } from "next";

import { Card, PageHeader, Section } from "@/components/ui";

export const metadata: Metadata = { title: "Architecture" };

const COMPONENTS = [
  ["GitHub", "Source, CI, experiment provenance and research management."],
  ["Kaggle", "Versioned dataset retrieval with the user's own credentials (M1)."],
  ["Google Colab", "Training and reproducible experiment notebooks calling package functions (M7)."],
  ["Hugging Face", "Evaluated model versions, matching preprocessing, model cards and an inference Space (M7)."],
  ["Vercel", "This portal, plus a server-side API boundary to the inference Space (M8)."],
] as const;

const PIPELINE = [
  "Dataset registry and license/provenance manifests",
  "SHA-256 source fingerprints",
  "Train/test split before any fitting",
  "Duplicate and target-leakage audit",
  "Train-only encoders, scalers, mutual-information selection and resampling",
  "Baseline training with recorded seeds and hyperparameters",
  "Evaluation on untouched test partitions",
  "Drift monitoring and adaptation simulation in time order",
  "Versioned result export consumed by this portal",
];

export default function ArchitecturePage() {
  return (
    <>
      <PageHeader
        title="Architecture"
        lede="A Python src-layout research package with typed configurations, and a separately deployable Next.js portal."
      />
      <Section title="Ecosystem">
        <div className="grid gap-4 sm:grid-cols-2">
          {COMPONENTS.map(([name, text]) => (
            <Card key={name} title={name}>
              <p>{text}</p>
            </Card>
          ))}
        </div>
      </Section>
      <Section title="Data and model pipeline">
        <ol className="list-decimal space-y-1 pl-6 text-ink-muted">
          {PIPELINE.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </Section>
      <Section title="API boundary">
        <p className="text-ink-muted">
          The browser never talks to Hugging Face directly and never receives a token. Requests
          go to a Vercel server route that validates the schema and request size, then forwards
          them to the inference Space with a server-held credential (planned for M8).
        </p>
      </Section>
    </>
  );
}
