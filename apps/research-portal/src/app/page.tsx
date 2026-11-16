import Link from "next/link";
import { TeamPortraits } from "@/components/TeamPortraits";
import { WorkflowExplainer } from "@/components/WorkflowExplainer";

import { Card, Section, StatusBadge } from "@/components/ui";
import { MILESTONES, REFERENCE_PAPER, RESEARCH_QUESTIONS } from "@/content/site";
import { resultsIndex } from "@/lib/results";

const STATUS_TEXT = { in_progress: "In progress", planned: "Planned", complete: "Complete" };

export default function HomePage() {
  const nResults = resultsIndex.results.length;
  return (
    <>
      <section className="relative mb-14 overflow-hidden rounded-3xl border border-[#294e76] text-white shadow-2xl shadow-[#07122b]/20">
        <div className="pointer-events-none absolute inset-0 bg-[#07152f]" />
        <div className="pointer-events-none absolute inset-0" style={{background:"radial-gradient(70% 85% at 0% 0%,rgba(34,108,199,.48),transparent 70%),radial-gradient(45% 75% at 100% 100%,rgba(177,34,52,.3),transparent 75%)"}}/>
        <div className="pointer-events-none absolute inset-0 opacity-[.06]" style={{backgroundImage:"linear-gradient(white 1px,transparent 1px),linear-gradient(90deg,white 1px,transparent 1px)",backgroundSize:"40px 40px"}}/>
        <div className="relative grid gap-9 px-6 py-11 sm:px-10 sm:py-14 lg:grid-cols-[1.15fr_.85fr] lg:items-center">
          <div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">CNT 6167 · Internet of Things</span>
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">Florida Atlantic University</span>
            </div>
            <h1 className="mt-6 max-w-2xl text-4xl font-extrabold leading-[1.09] tracking-tight sm:text-5xl">Intrusion detection that <span className="bg-gradient-to-r from-[#85d7ff] via-[#c6dcff] to-white bg-clip-text text-transparent">adapts as IoT traffic changes.</span></h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-white/75 sm:text-lg">DriftGuard-IoT explores leakage-safe learning, delayed labels, and resource-conscious model updates at the edge. Follow our research paper and the two CNT 6167 presentations.</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/presentation-2" className="rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#07152f] transition hover:bg-sky-50">Explore Presentation 2 ↗</Link>
              <Link href="/paper" className="rounded-xl border border-white/25 bg-white/10 px-5 py-3 text-sm font-semibold backdrop-blur transition hover:bg-white/20">Read the paper</Link>
              <Link href="/presentation-1" className="rounded-xl border border-white/25 bg-white/10 px-5 py-3 text-sm font-semibold backdrop-blur transition hover:bg-white/20">Presentation 1</Link>
            </div>
            <p className="mt-5 text-xs text-white/55">Arun Kumar Gharami & Ankith Gajam · Presentation 2 · Professor Mohammad Ilyas</p>
          </div>
          <div className="rounded-2xl border border-white/20 bg-white/[.07] p-5 shadow-xl backdrop-blur-md">
            <p className="mb-4 text-[11px] font-bold uppercase tracking-[.18em] text-[#acdafa]">IoT edge security workflow</p>
            <div className="space-y-2 text-sm">
              <div className="rounded-xl border border-white/15 bg-white/10 px-4 py-3"><strong className="block">01 · Devices & telemetry</strong><span className="text-xs text-white/60">Sensors / MQTT streams / time-ordered flow events</span></div>
              <div className="mx-auto h-3 w-px bg-[#93b9df]"/>
              <div className="rounded-xl border border-white/15 bg-white/10 px-4 py-3"><strong className="block">02 · Edge gateway IDS</strong><span className="text-xs text-white/60">Preprocess → inference → event audit</span></div>
              <div className="mx-auto h-3 w-px bg-[#93b9df]"/>
              <div className="rounded-xl border border-[#f18b9b]/45 bg-[#a82439]/25 px-4 py-3"><strong className="block">03 · Drift + delayed labels</strong><span className="text-xs text-white/65">ADWIN signals / eligible ground truth / policies</span></div>
              <div className="mx-auto h-3 w-px bg-[#93b9df]"/>
              <div className="rounded-xl border border-sky-200/40 bg-sky-400/15 px-4 py-3"><strong className="block">04 · Bounded adaptation</strong><span className="text-xs text-white/65">Controlled retraining and measurable resource costs</span></div>
            </div>
            <p className="mt-4 text-[11px] leading-relaxed text-white/55">Research architecture; physical edge and real-data validation remain separate evidence gates.</p>
          </div>
        </div>
        <div className="relative grid grid-cols-2 border-t border-white/15 bg-black/20 sm:grid-cols-4">
          {[["2","Course presentations"],["21","Slides in Presentation 2"],["5","Adaptation policies studied"],[String(nResults),"Reportable results recorded"]].map(([v,l])=><div key={l} className="border-r border-white/10 px-5 py-4 last:border-r-0 sm:px-7"><p className="text-2xl font-extrabold tabular-nums">{v}</p><p className="text-xs text-white/55">{l}</p></div>)}
        </div>
      </section>

      <section aria-labelledby="presentation-showcase" className="mb-12">
        <h2 id="presentation-showcase" className="mb-5 text-2xl font-bold tracking-tight sm:text-3xl">Our research presentations</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <article className="rounded-2xl border border-line bg-surface-muted p-6">
            <p className="text-xs font-medium uppercase tracking-widest text-accent">First · October 2026</p>
            <h3 className="mt-2 text-xl font-semibold">Presentation 1 — Reference paper review</h3>
            <p className="mt-3 text-sm text-ink-muted">Explore the 25-slide review of lightweight IoT intrusion detection, original group credits, and the archived slide-folder link.</p>
            <Link href="/presentation-1" className="mt-5 inline-block rounded-lg border border-line px-4 py-2 font-medium">Explore Presentation 1</Link>
          </article>
          <article className="rounded-2xl border border-[#45739a] bg-gradient-to-br from-[#143856] to-[#132236] p-6">
            <p className="text-xs font-medium uppercase tracking-widest text-[#a2daf1]">Second · Fall 2026</p>
            <h3 className="mt-2 text-xl font-semibold text-white">Presentation 2 — DriftGuard-IoT research</h3>
            <p className="mt-3 text-sm text-[#d4e0ed]">Arun Kumar Gharami and Ankith Gajam present the paper, drift-aware edge workflow, research mind map and available materials.</p>
            <Link href="/presentation-2" className="mt-5 inline-block rounded-lg bg-white px-4 py-2 font-semibold text-[#102a44]">Explore Presentation 2</Link>
            <Link href="/paper" className="ml-3 mt-5 inline-block text-sm text-white underline underline-offset-4">Read full paper</Link>
          </article>
        </div>
      </section>
      <WorkflowExplainer />
      <TeamPortraits />

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
