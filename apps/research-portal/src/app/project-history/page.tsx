import type { Metadata } from "next";
import Link from "next/link";
import { PageHeader } from "@/components/ui";
import { JOURNEY } from "@/content/group";

export const metadata: Metadata = { title: "Our project history" };

export default function ProjectHistoryPage() {
  return <>
    <PageHeader title="How we established DriftGuard-IoT" lede="Our Grad1 journey, from a course paper review to a reproducible IoT research project." />
    <p className="mb-8 max-w-3xl text-ink-muted">Each stage records the challenge, the work that followed and the evidence available. Merged software and synthetic checks do not establish research performance.</p>
    <ol className="space-y-6 border-l-2 border-line pl-5 sm:pl-8">
      {JOURNEY.map((stage, index) => <li key={stage.title} className="rounded-xl border border-line bg-surface-muted p-5 sm:p-7">
        <p className="text-sm font-medium text-accent">{String(index + 1).padStart(2, "0")} / {stage.date}</p>
        <h2 className="mt-2 text-xl font-semibold">{stage.title}</h2>
        <p className="mt-2 text-xs font-medium uppercase tracking-wide text-research">{stage.status}</p>
        <p className="mt-4 leading-relaxed text-ink-muted">{stage.detail}</p>
        <p className="mt-4 text-sm">{stage.source ? <a className="underline underline-offset-4" href={stage.source}>{stage.sourceLabel}</a> : stage.sourceLabel}</p>
      </li>)}
    </ol>
    <p className="mt-8"><Link className="underline underline-offset-4" href="/presentation-1">Review Presentation 1</Link></p>
  </>;
}
