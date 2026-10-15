import Link from "next/link";
import { WorkflowExplainer } from "@/components/WorkflowExplainer";

import { Card, Section, StatusBadge } from "@/components/ui";
import { MILESTONES, REFERENCE_PAPER, RESEARCH_QUESTIONS } from "@/content/site";
import { resultsIndex } from "@/lib/results";

const STATUS_TEXT = { in_progress: "In progress", planned: "Planned", complete: "Complete" };

export default function HomePage() {
  const nResults = resultsIndex.results.length;
  return (
    <>
      <div className="mb-12 space-y-5">
        <p className="text-sm font-medium uppercase tracking-wider text-accent">
          IoT / IIoT intrusion detection research
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Trustworthy, drift-aware and resource-efficient intrusion detection
        </h1>
        <p className="max-w-3xl text-lg text-ink-muted">
          We are Grad1, a three-member CNT 6167 team at Florida Atlantic University.
          Our project builds a leakage-safe reproduction framework for five lightweight
          intrusion-detection baselines. We plan to evaluate drift monitoring and adaptation
          across IoT and IIoT environments using verified benchmark data.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/presentation-1" className="rounded border border-line px-4 py-2 font-medium">Presentation 1</Link>
          <Link href="/project-history" className="rounded border border-line px-4 py-2 font-medium">Our project journey</Link>
          <Link href="/team" className="rounded border border-line px-4 py-2 font-medium">Meet Grad1</Link>
          <Link
            href="/research"
            className="rounded bg-accent px-4 py-2 font-medium text-accent-ink hover:opacity-90"
          >
            Research questions
          </Link>
          <Link href="/reproducibility" className="rounded border border-line px-4 py-2 font-medium">
            Reproducibility
          </Link>
        </div>
      </div>

      <WorkflowExplainer />

      <div
        role="status"
        className="mb-12 rounded-lg border border-line bg-surface-muted p-5 text-sm"
      >
        <p className="font-medium">
          Recorded research results: {nResults === 0 ? "none yet" : nResults}
        </p>
        <p className="mt-1 text-ink-muted">
          The repository includes baseline infrastructure and a synthetic MQTT workflow.
          No reportable benchmark results are recorded here. Software progress and
          simulated demonstrations are tracked separately from research evidence.
        </p>
      </div>

      <Section title="Research questions">
        <ol className="grid gap-3 sm:grid-cols-2">
          {RESEARCH_QUESTIONS.map((q) => (
            <li key={q.id} className="rounded-lg border border-line p-4">
              <span className="font-mono text-sm text-accent">{q.id}</span>
              <p className="mt-1">{q.text}</p>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="Milestones">
        <ol className="divide-y divide-line rounded-lg border border-line">
          {MILESTONES.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-4 px-4 py-3">
              <span>
                <span className="mr-3 font-mono text-sm text-ink-muted">{m.id}</span>
                {m.title}
              </span>
              <StatusBadge
                kind={m.status === "complete" ? "research" : "planned"}
                label={STATUS_TEXT[m.status]}
              />
            </li>
          ))}
        </ol>
      </Section>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card title="Reference study">
          <p>{REFERENCE_PAPER.citation}</p>
          <p>
            <a className="underline" href={`https://doi.org/${REFERENCE_PAPER.doi}`}>
              doi:{REFERENCE_PAPER.doi}
            </a>
          </p>
        </Card>
        <Card title="What is not claimed">
          <p>
            No novelty is claimed before the literature review is complete, and no superiority
            is claimed before experiments are run and verified.
          </p>
        </Card>
      </div>
    </>
  );
}
