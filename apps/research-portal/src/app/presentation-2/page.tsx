import type { Metadata } from "next";
import Link from "next/link";
import { PageHeader, StatusBadge } from "@/components/ui";
import { PersonPortrait } from "@/components/PersonPortrait";
import { PORTRAITS } from "@/content/portraits";
import { PresentationMediaStudio } from "@/components/PresentationMediaStudio";

export const metadata: Metadata = {
  title: "Presentation 2",
  description: "DriftGuard-IoT research presentation two: paper, edge-IoT security workflow, resources and presenters Arun Kumar Gharami and Ankith Gajam."
};

const paperFigures = [
  { name: "Device-to-edge architecture", src: "/paper/fig_architecture.png", description: "ESP32 sensing, MQTT, gateway inference and the proposed adaptation loop." },
  { name: "IoT sensor hardware", src: "/paper/fig_circuit.png", description: "Documented ESP32 sensor-node and supporting power circuitry." },
  { name: "Post-drift evaluation", src: "/paper/fig_f1_post.png", description: "Controlled synthetic study — not field-validated benchmark performance." },
  { name: "Drift response traces", src: "/paper/fig_traces.png", description: "Controlled synthetic simulation of adaptation-policy behavior." },
];

const mindMap = [
  { title: "Why IoT IDS drifts", items: ["Nonstationary telemetry and attack patterns", "Static classifier degradation", "Delayed verified labels"] },
  { title: "Device-to-cloud workflow", items: ["ESP32 and sensor input", "MQTT flow messages", "Edge gateway classifier", "Monitoring and dashboard"] },
  { title: "Adaptation strategy", items: ["Prediction and error audit", "ADWIN drift signal", "Delayed label availability", "Bounded-window model refit"] },
  { title: "Evidence & evaluation", items: ["Chronological and leakage-safe splits", "Macro-F1, recall, FPR", "Latency, memory and retraining cost", "Synthetic study versus real-world validation"] },
  { title: "Research roadmap", items: ["Authorized real IoT/IIoT datasets", "Reproducibility and ablations", "Physical hardware measurements", "Deployment limitations"] },
];

function ResourceCard({title,description,href,status}:{title:string;description:string;href?:string;status?:string}) {
  return <article className="flex h-full flex-col rounded-2xl border border-line bg-surface-muted p-5 shadow-sm">
    <div className="mb-3 flex items-center justify-between gap-2"><h3 className="font-semibold">{title}</h3><span className="rounded-full border border-line px-2 py-1 text-xs text-ink-muted">{status ?? (href ? "Available" : "Pending file")}</span></div>
    <p className="mb-5 flex-1 text-sm leading-relaxed text-ink-muted">{description}</p>
    {href ? <Link href={href} className="inline-flex min-h-11 items-center justify-center rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-ink hover:opacity-90">Open {title}<span className="sr-only"> resource</span></Link>
      : <span className="inline-flex min-h-11 items-center justify-center rounded-lg border border-line px-4 py-2 text-sm text-ink-muted" aria-label={title + " upload pending"}>Awaiting published file</span>}
  </article>;
}

export default function PresentationTwoPage(){
  return <div className="space-y-12">
    <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-[#123d66] via-[#0b223d] to-[#121b30] px-6 py-10 sm:px-10 sm:py-14">
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#d13c55]/15 blur-3xl" />
      <p className="mb-4 text-xs font-bold uppercase tracking-[.22em] text-[#f8bdc7]">Florida Atlantic University · CNT 6167 · Fall 2026</p>
      <h1 className="max-w-3xl text-3xl font-bold leading-tight tracking-tight text-white sm:text-5xl">Presentation 2 <span className="block text-[#98e0f0]">DriftGuard-IoT</span></h1>
      <p className="mt-5 max-w-2xl text-base leading-relaxed text-[#d9e5f3]">Drift-aware and resource-efficient adaptation for intelligent IoT intrusion detection. Our technical research overview connects network telemetry, edge classification, delayed labels, statistical drift monitoring and bounded adaptation.</p>
      <p className="mt-5 text-sm text-white"><strong>Presented by:</strong> Arun Kumar Gharami and Ankith Gajam</p>
      <p className="mt-1 text-sm text-[#d9e5f3]"><strong>Presented to:</strong> Professor Mohammad Ilyas, PhD · Course instructor</p>
      <div className="mt-7 flex flex-wrap gap-3"><Link href="/paper" className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-[#0b2545]">Read research paper</Link><Link href="/presentation-1" className="rounded-lg border border-[#8195ac] px-5 py-3 text-sm font-semibold text-white">View Presentation 1</Link></div>
    </div>

    <PresentationMediaStudio />

    <section aria-labelledby="materials-heading" className="space-y-5">
      <div><h2 id="materials-heading" className="text-2xl font-semibold">Presentation 2 · Research materials</h2><p className="mt-2 text-sm text-ink-muted">The complete 21-slide deck is available through Google Slides (access follows its sharing settings). Videos and the infographic require stable public hosting before embedded playback or downloads can be enabled.</p></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ResourceCard title="Research paper" href="/paper" description="Complete manuscript, documented methods, figures, simulation labels and references." />
        <ResourceCard title="Presentation video" description="Second 10-minute research presentation. MP4 files were supplied for review but are not yet hosted at a stable public URL." />
        <ResourceCard title="Presentation slides" href="https://docs.google.com/presentation/d/1LTQs5JwvnbwJjxSYeeAMVchC1KtSeYXUo8eW5Hakgmo/edit?usp=drivesdk" description="Open the complete 21-slide FAU research presentation by Arun Kumar Gharami and Ankith Gajam. Slides cover architecture, MQTT, drift detection, evidence, resource limits and validation roadmap. Google Drive sharing permissions apply." status="21 slides · Google Slides" />
        <ResourceCard title="Research infographic" description="The uploaded IoT Intrusion Detection research poster is awaiting a public asset URL for full-resolution viewing." />
        <ResourceCard title="Interactive mind map" href="#mind-map" description="Expandable research topics covering problem, architecture, adaptation, evaluation and next steps." status="Live below" />
        <ResourceCard title="Source repository" href="https://github.com/Arungharami/DriftGuard-IoT" description="Versioned implementation, research documentation and reproducibility resources." />
      </div>
    </section>

    <section aria-labelledby="workflow-heading" className="space-y-5">
      <div><h2 id="workflow-heading" className="text-2xl font-semibold">How the research system works</h2><p className="mt-2 max-w-3xl text-ink-muted">The pipeline shown below combines documented software concepts and proposed adaptation experiments. Individual stages are not claims of completed physical hardware validation.</p></div>
      <ol className="grid gap-3 md:grid-cols-3">
        {["01 · Capture MQTT and sensor flows","02 · Extract features and predict","03 · Audit errors as labels arrive","04 · Monitor drift with ADWIN","05 · Evaluate bounded model refit","06 · Compare detection and edge costs"].map((step)=> <li key={step} className="rounded-xl border border-line bg-surface-muted p-4 text-sm font-medium">{step}</li>)}
      </ol>
      <div className="grid gap-4 sm:grid-cols-2">{paperFigures.map((f)=> <figure key={f.src} className="overflow-hidden rounded-xl border border-line bg-surface-muted"><a href={f.src} target="_blank" rel="noreferrer" className="block"><img src={f.src} alt={f.description} className="aspect-[16/9] w-full object-contain p-3" loading="lazy" /></a><figcaption className="border-t border-line p-4"><strong className="block text-sm">{f.name}</strong><span className="mt-1 block text-xs text-ink-muted">{f.description}</span></figcaption></figure>)}</div>
      <p className="text-xs text-ink-muted">Figures are sourced from the existing manuscript assets. Simulation figures should never be described as field measurements. See the full paper for captions and methodology.</p>
    </section>

    <section id="mind-map" aria-labelledby="mind-map-heading" className="scroll-mt-8 space-y-5">
      <div><h2 id="mind-map-heading" className="text-2xl font-semibold">Interactive research mind map</h2><p className="mt-2 text-sm text-ink-muted">Expand each branch to review the key research decisions and evidence boundaries.</p></div>
      <div className="rounded-2xl border border-[#5b85a8] bg-gradient-to-r from-[#102a44] to-[#0b1e31] p-5 text-center"><span className="text-lg font-bold text-white">DriftGuard-IoT</span><p className="text-xs text-[#c5d7e8]">Telemetry → IDS → Drift → Delayed labels → Resource-aware adaptation</p></div>
      <div className="grid gap-4 md:grid-cols-2">{mindMap.map((branch)=> <details key={branch.title} open={branch.title === "Device-to-cloud workflow"} className="group rounded-xl border border-line bg-surface-muted p-4"><summary className="cursor-pointer font-semibold marker:text-accent">{branch.title}</summary><ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-ink-muted">{branch.items.map((item)=><li key={item}>{item}</li>)}</ul></details>)}</div>
    </section>

    <section aria-labelledby="status-heading" className="rounded-2xl border border-line bg-surface-muted p-6">
      <h2 id="status-heading" className="text-xl font-semibold">Evidence and research status</h2>
      <p className="mt-3 text-sm leading-relaxed text-ink-muted">This presentation discusses the paper's controlled synthetic stream evaluation and the project's software workflow. Synthetic accuracy, latency and retraining comparisons are not independently verified real-world IDS deployment results. Benchmark dataset validation and physical edge measurements require separate evidence.</p>
      <div className="mt-4 flex flex-wrap gap-3"><StatusBadge kind="simulated" label="Synthetic stream analysis" /><StatusBadge kind="planned" label="Physical benchmarking pending" /><Link className="text-sm underline underline-offset-4" href="/reproducibility">Review reproducibility</Link></div>
    </section>

    <section aria-labelledby="team-heading" className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[.2em] text-accent">Our people</p>
          <h2 id="team-heading" className="mt-2 text-2xl font-semibold tracking-tight">Presentation 2 · Presenters and instructor</h2>
          <p className="mt-2 max-w-2xl text-sm text-ink-muted">Two graduate co-presenters, with course instruction from Professor Mohammad Ilyas.</p>
        </div>
        <Link href="/paper" className="text-sm font-medium text-accent underline underline-offset-4">Research paper ↗</Link>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <article className="group rounded-2xl border border-line bg-surface-muted p-5 transition-colors hover:border-[#5c91b4]">
          <div className="flex items-start gap-4">
            <div className="w-[78px] shrink-0 sm:w-[88px] [&>div]:mb-0 [&>div]:rounded-xl">
              <PersonPortrait name="Arun Kumar Gharami" src={PORTRAITS["Arun Kumar Gharami"]?.src}/>
            </div>
            <div className="min-w-0 pt-1">
              <p className="text-[11px] font-bold uppercase tracking-widest text-[#8be1d3]">Co-presenter · Grad1</p>
              <h3 className="mt-1 text-lg font-semibold leading-snug">Arun Kumar Gharami</h3>
              <p className="mt-1 text-xs text-ink-muted">Florida Atlantic University</p>
            </div>
          </div>
          <div className="mt-5 border-t border-line pt-4">
            <a className="inline-flex min-h-10 items-center rounded-lg border border-line px-3 text-sm font-medium hover:bg-[#274055] focus-visible:outline" href="https://huggingface.co/arun-gharami" target="_blank" rel="noopener noreferrer">Public profile & photo source <span aria-hidden="true" className="ml-2">↗</span></a>
          </div>
        </article>
        <article className="group rounded-2xl border border-line bg-surface-muted p-5 transition-colors hover:border-[#5c91b4]">
          <div className="flex items-start gap-4">
            <div className="w-[78px] shrink-0 sm:w-[88px] [&>div]:mb-0 [&>div]:rounded-xl">
              <PersonPortrait name="Ankith Gajam"/>
            </div>
            <div className="min-w-0 pt-1">
              <p className="text-[11px] font-bold uppercase tracking-widest text-[#8be1d3]">Co-presenter · Grad1</p>
              <h3 className="mt-1 text-lg font-semibold leading-snug">Ankith Gajam</h3>
              <p className="mt-1 text-xs text-ink-muted">Portrait pending · No generated photo</p>
            </div>
          </div>
          <div className="mt-5 border-t border-line pt-4">
            <a className="inline-flex min-h-10 items-center rounded-lg border border-line px-3 text-sm font-medium hover:bg-[#274055] focus-visible:outline" href="https://www.linkedin.com/in/ankithgajam/" target="_blank" rel="noopener noreferrer">LinkedIn profile <span aria-hidden="true" className="ml-2">↗</span></a>
          </div>
        </article>
        <article className="rounded-2xl border border-[#38546c] bg-gradient-to-br from-[#142a40] to-[#0e1b2c] p-5">
          <div className="flex items-start gap-4">
            <div className="w-[78px] shrink-0 sm:w-[88px] [&>div]:mb-0 [&>div]:rounded-xl">
              <PersonPortrait name="Professor Mohammad Ilyas" src={PORTRAITS["Professor Mohammad Ilyas"]?.src}/>
            </div>
            <div className="min-w-0 pt-1">
              <p className="text-[11px] font-bold uppercase tracking-widest text-[#f2c5a2]">Course instructor</p>
              <h3 className="mt-1 text-lg font-semibold leading-snug">Professor Mohammad Ilyas</h3>
              <p className="mt-1 text-xs text-ink-muted">CNT 6167 · FAU</p>
            </div>
          </div>
          <div className="mt-5 border-t border-[#38546c] pt-4">
            <a className="inline-flex min-h-10 items-center rounded-lg border border-[#38546c] px-3 text-sm font-medium hover:bg-[#274055] focus-visible:outline" href="https://www.fau.edu/engineering/directory/faculty/ilyas/" target="_blank" rel="noopener noreferrer">Official FAU profile <span aria-hidden="true" className="ml-2">↗</span></a>
          </div>
        </article>
      </div>
      <p className="text-xs leading-relaxed text-ink-muted">Professor Ilyas is the course instructor, not a student team member. The original Presentation 1 credits remain preserved; Presentation 2 features Arun and Ankith.</p>
    </section>
  </div>;
}
