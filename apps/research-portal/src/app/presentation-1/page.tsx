import type { Metadata } from "next";
import Link from "next/link";

import { PRESENTATION_FOLDER, SLIDE_REVIEW } from "@/content/group";

export const metadata: Metadata = { title: "Presentation 1 review" };

export default function PresentationOnePage() {
  return <>
    <div className="mb-9 rounded-3xl border border-line bg-gradient-to-br from-[#0e3b64] via-[#112941] to-[#101a30] p-7 shadow-sm sm:p-10">
      <p className="text-xs font-bold uppercase tracking-[.2em] text-[#d7eafd]">Florida Atlantic University · CNT 6167 · Fall 2026</p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">Presentation 1 <span className="block text-[#a7e1ed]">Lightweight IDS Paper Review</span></h1>
      <p className="mt-4 max-w-3xl leading-relaxed text-[#dbe9f4]">Our original Grad1 paper review of intrusion detection for IoT and IIoT, including the comparative study, implementation update, and future research questions.</p>
      <div className="mt-6 flex flex-wrap gap-3">
        <a className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-[#102b48]" href={PRESENTATION_FOLDER}>Open archived slides folder</a>
        <Link className="rounded-lg border border-[#7fa3c2] px-4 py-2 text-sm font-semibold text-white" href="/presentation-2">Continue to Presentation 2</Link>
      </div>
    </div>
    <div className="mb-8 rounded-xl border border-line bg-surface-muted p-6">
      <p className="text-sm font-medium text-accent">CNT 6167 / Professor Mohammad Ilyas</p>
      <h2 className="mt-3 text-2xl font-semibold">Our first shared presentation</h2>
      <p className="mt-3 text-ink-muted">Arun Kumar Gharami, Shefatha Rabbany and Ankith Gajam. This page provides a concise text review of the existing 25-slide deck. It is not a rendering of the PowerPoint file.</p>
      <a className="mt-5 inline-block rounded bg-accent px-4 py-2 font-medium text-accent-ink" href={PRESENTATION_FOLDER}>Open team PowerPoint and recordings folder</a>
      <p className="mt-3 text-sm text-ink-muted">Google Drive access follows the folder’s existing sharing settings.</p>
    </div>
    <aside className="mb-8 border-l-4 border-research pl-4 text-sm leading-relaxed text-ink-muted" aria-label="Presentation evidence note">Reported paper findings belong to Ismail et al. Our implementation and synthetic demonstrations are separate. Proposed experiments and hardware measurements remain unverified. The deck contains inconsistent speaker assignments, so final individual responsibilities need team review.</aside>
    <section aria-labelledby="slide-review">
      <h2 id="slide-review" className="mb-4 text-xl font-semibold">Slide-by-slide review</h2>
      <ol className="space-y-3">{SLIDE_REVIEW.map(([title, summary], index) => <li key={title}>
        <details className="rounded-lg border border-line p-4 open:bg-surface-muted">
          <summary className="cursor-pointer font-medium"><span className="mr-3 font-mono text-sm text-accent">{String(index + 1).padStart(2, "0")}</span>{title}</summary>
          <p className="mt-3 max-w-3xl leading-relaxed text-ink-muted">{summary}</p>
        </details>
      </li>)}</ol>
    </section>
    <p className="mt-8 text-sm text-ink-muted">Source deck: Grad1_Final_Presentation_Arun_Updated.pptx, October 7, 2026. Reference study: <a className="underline" href="https://doi.org/10.1109/ACCESS.2025.3554083">Ismail, Dandan and Qushou (2025)</a>.</p>
  </>;
}
