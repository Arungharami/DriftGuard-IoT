import type { Metadata } from "next";
import Link from "next/link";

import { Card, PageHeader, Section } from "@/components/ui";

export const metadata: Metadata = {
  title: "Related Research · DriftCVE-NLP",
  description:
    "A companion NLP research project studying temporal drift in CVE-to-CWE classification and vulnerability retrieval.",
};

const driftCveUrl = "https://driftcve-nlp.vercel.app/";
const paperUrl = "https://driftcve-nlp.vercel.app/paper/driftcve.pdf";
const repoUrl = "https://github.com/Arungharami/DriftCVE-NLP";

export default function RelatedResearchPage() {
  return (
    <>
      <PageHeader
        title="Related Research: DriftCVE-NLP"
        lede="A companion research project exploring a closely related problem in a different data domain: how temporal change affects cybersecurity language models and vulnerability retrieval."
      />

      <section className="mb-10 overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-surface-muted via-surface to-surface-muted p-6 sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">
          Companion research · NLP + vulnerability intelligence
        </p>
        <h2 className="mt-3 max-w-3xl text-2xl font-semibold tracking-tight sm:text-3xl">
          Do vulnerability classifiers and retrievers survive time?
        </h2>
        <p className="mt-4 max-w-3xl leading-7 text-ink-muted">
          DriftCVE-NLP studies CVE-to-CWE classification and CVE retrieval under temporal
          language drift. Its portal documents a time-aware protocol, dataset construction,
          model comparisons, drift diagnostics, error analysis, and reproducibility resources.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <a href={driftCveUrl} target="_blank" rel="noreferrer" className="rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-accent-ink hover:opacity-90">
            Explore DriftCVE-NLP ↗
          </a>
          <a href={paperUrl} target="_blank" rel="noreferrer" className="rounded-lg border border-line px-4 py-2.5 text-sm font-semibold hover:bg-surface-muted">
            Read working-draft PDF ↗
          </a>
          <a href={repoUrl} target="_blank" rel="noreferrer" className="rounded-lg border border-line px-4 py-2.5 text-sm font-semibold hover:bg-surface-muted">
            View source repository ↗
          </a>
        </div>
        <p className="mt-4 text-xs text-ink-muted">
          The linked manuscript is identified by its source portal as a working draft, not a
          peer-reviewed publication.
        </p>
      </section>

      <Section title="Research at a glance">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card title="Research task">
            <p className="text-sm leading-6 text-ink-muted">
              Map natural-language CVE descriptions to Common Weakness Enumeration (CWE)
              labels, and retrieve related vulnerability records.
            </p>
          </Card>
          <Card title="Temporal protocol">
            <p className="text-sm leading-6 text-ink-muted">
              Train on 2018–2023 descriptions, tune on 2024, then report 2024, 2025, and
              partial 2026 separately rather than pooling future periods.
            </p>
          </Card>
          <Card title="Model families">
            <p className="text-sm leading-6 text-ink-muted">
              Majority and bag-of-words baselines, word and character TF-IDF with linear
              classifiers, MiniLM embeddings with logistic regression, and a DistilBERT
              fine-tuning track.
            </p>
          </Card>
        </div>
      </Section>

      <Section title="What the research investigates">
        <div className="grid gap-4 md:grid-cols-2">
          <Card title="Temporal generalization">
            <p className="text-sm leading-6 text-ink-muted">
              Compare later-year classification performance with the validation period and
              examine which model families remain stable as vulnerability language changes.
            </p>
          </Card>
          <Card title="Label-prior shift">
            <p className="text-sm leading-6 text-ink-muted">
              Compare raw accuracy with accuracy standardized to training class priors. This
              helps separate changes in class composition from changes in within-class
              recognition.
            </p>
          </Card>
          <Card title="Language drift diagnostics">
            <p className="text-sm leading-6 text-ink-muted">
              Track vocabulary and label-distribution change with Jensen–Shannon divergence,
              alongside bigram language-model perplexity and embedding-space diagnostics.
            </p>
          </Card>
          <Card title="Retrieval and error analysis">
            <p className="text-sm leading-6 text-ink-muted">
              Evaluate sparse and dense retrieval on known CVEs, inspect top-k outcomes, and
              review class confusions and saved misclassified examples.
            </p>
          </Card>
        </div>
      </Section>

      <Section title="Why it matters alongside DriftGuard-IoT">
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="bg-surface-muted text-ink-muted">
              <tr>
                <th className="p-3 font-medium">Dimension</th>
                <th className="p-3 font-medium">DriftCVE-NLP</th>
                <th className="p-3 font-medium">DriftGuard-IoT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              <tr><th className="p-3 font-medium">Input domain</th><td className="p-3 text-ink-muted">CVE text and vulnerability descriptions</td><td className="p-3 text-ink-muted">IoT / IIoT network and device telemetry</td></tr>
              <tr><th className="p-3 font-medium">Prediction task</th><td className="p-3 text-ink-muted">CVE-to-CWE classification and retrieval</td><td className="p-3 text-ink-muted">Intrusion detection across traffic classes</td></tr>
              <tr><th className="p-3 font-medium">Change of interest</th><td className="p-3 text-ink-muted">Temporal language and label-distribution change</td><td className="p-3 text-ink-muted">Temporal and cross-domain telemetry drift</td></tr>
              <tr><th className="p-3 font-medium">Resource focus</th><td className="p-3 text-ink-muted">NLP model and retrieval behavior</td><td className="p-3 text-ink-muted">Edge latency, memory, throughput, and adaptation cost</td></tr>
            </tbody>
          </table>
        </div>
        <p className="mt-4 max-w-4xl text-sm leading-6 text-ink-muted">
          The projects are complementary, not one combined experiment. DriftCVE-NLP provides
          a useful comparison for thinking about temporal evaluation, class-prior changes,
          reproducible splits, and error analysis. Its results do not establish that the same
          detectors or thresholds will work on IoT traffic; that would require separate
          experiments on the DriftGuard datasets.
        </p>
      </Section>

      <Section title="Research questions this connection suggests">
        <ol className="grid gap-3 sm:grid-cols-2">
          <li className="rounded-xl border border-line p-4"><span className="font-mono text-sm text-accent">01</span><p className="mt-2 text-sm leading-6">Can temporal evaluation protocols be made comparable across text-based vulnerability intelligence and streaming IoT telemetry?</p></li>
          <li className="rounded-xl border border-line p-4"><span className="font-mono text-sm text-accent">02</span><p className="mt-2 text-sm leading-6">How should evaluation distinguish label-prior changes from changes in the conditional difficulty of recognizing a class?</p></li>
          <li className="rounded-xl border border-line p-4"><span className="font-mono text-sm text-accent">03</span><p className="mt-2 text-sm leading-6">Which drift indicators remain useful when labels are delayed, incomplete, or expensive to obtain?</p></li>
          <li className="rounded-xl border border-line p-4"><span className="font-mono text-sm text-accent">04</span><p className="mt-2 text-sm leading-6">How can adaptation gains be reported together with compute, memory, latency, and false-alarm costs?</p></li>
        </ol>
        <p className="mt-4 text-xs text-ink-muted">
          These are cross-project research directions, not completed findings or claims of
          shared experimental validation.
        </p>
      </Section>

      <Section title="Video overview">
        <div className="rounded-xl border border-dashed border-line bg-surface-muted p-6">
          <p className="font-semibold">Video embed awaiting the exported video URL</p>
          <p className="mt-2 text-sm leading-6 text-ink-muted">
            The DriftGuard-IoT NotebookLM video workspace is known, but an exported,
            publicly accessible video URL or MP4 asset is not yet available in the project
            materials. The player can be added here as soon as that exact video link is
            supplied.
          </p>
        </div>
      </Section>

      <div className="flex flex-wrap gap-3 border-t border-line pt-6 text-sm">
        <Link href="/publications" className="underline underline-offset-4">Back to publications</Link>
        <Link href="/research" className="underline underline-offset-4">Explore DriftGuard research questions</Link>
      </div>
    </>
  );
}
