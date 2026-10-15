import type { Metadata } from "next";
import { PageHeader } from "@/components/ui";
import { PRESENTATION_FOLDER, SLIDE_REVIEW } from "@/content/group";

export const metadata: Metadata = { title: "Presentation 1 review" };

export default function PresentationOnePage() {
  return <>
    <PageHeader title="Presentation 1" lede="Grad1’s review of lightweight intrusion detection for IoT and IIoT, with our implementation update and proposed next steps." />
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
