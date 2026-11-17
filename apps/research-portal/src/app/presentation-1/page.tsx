import type { Metadata } from "next";
import Link from "next/link";
import { PRESENTATION_FOLDER } from "@/content/group";
import { PresentationOneViewer } from "@/components/PresentationOneViewer";

export const metadata: Metadata = {
  title: "Presentation 1 | Lightweight IoT Intrusion Detection",
  description: "Original Grad1 CNT 6167 presentation: interactive 25-slide paper review, research critique and project development context."
};

export default function PresentationOnePage() {
  return <div className="space-y-14 pb-12">
    <section className="relative overflow-hidden rounded-3xl border border-[#315a82] text-white shadow-xl">
      <div className="pointer-events-none absolute inset-0 bg-[#081a32]" />
      <div className="pointer-events-none absolute inset-0" style={{background:"radial-gradient(70% 95% at 0% 0%,rgba(41,115,193,.58),transparent 72%),radial-gradient(55% 90% at 100% 100%,rgba(181,33,62,.26),transparent 70%)"}}/>
      <div className="relative grid gap-7 px-6 py-11 sm:px-10 sm:py-14 lg:grid-cols-[1.3fr_.7fr] lg:items-center">
        <div>
          <div className="flex flex-wrap gap-2 text-xs font-semibold"><span className="rounded-full border border-white/20 bg-white/10 px-3 py-1">Florida Atlantic University</span><span className="rounded-full border border-white/20 bg-white/10 px-3 py-1">CNT 6167 · Fall 2026</span><span className="rounded-full bg-[#c33650] px-3 py-1">Presentation 1</span></div>
          <h1 className="mt-6 max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl">Lightweight Intrusion Detection <span className="block text-[#a5def1]">for IoT and IIoT</span></h1>
          <p className="mt-5 max-w-2xl leading-relaxed text-white/75">Our original Grad1 team presentation reviews a published IDS benchmark study, assesses its methodology and limitations, and connects its findings to our DriftGuard-IoT development roadmap.</p>
          <div className="mt-7 flex flex-wrap gap-3"><a href="#slide-explorer" className="rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#0c2c4d]">Explore 25 slides ↓</a><a href={PRESENTATION_FOLDER} target="_blank" rel="noopener noreferrer" className="rounded-xl border border-white/30 bg-white/10 px-5 py-3 text-sm font-semibold">Original PPT & recordings ↗</a><Link href="/presentation-2" className="rounded-xl border border-white/30 bg-white/10 px-5 py-3 text-sm font-semibold">Presentation 2 →</Link></div>
        </div>
        <aside className="rounded-2xl border border-white/20 bg-white/[.08] p-5 backdrop-blur">
          <p className="text-[11px] font-bold uppercase tracking-[.17em] text-sky-200">Original Grad1 team</p>
          <div className="mt-4 space-y-3">{["Arun Kumar Gharami","Shefatha Rabbany","Ankith Gajam"].map((name,i)=><div key={name} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/10 px-3 py-2.5"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#315a83] text-xs font-bold">{String(i+1).padStart(2,"0")}</span><span className="text-sm font-semibold">{name}</span></div>)}</div>
          <p className="mt-4 text-xs leading-relaxed text-white/65">Presented for Professor Mohammad Ilyas, CNT 6167. Original group membership is preserved for historical accuracy.</p>
        </aside>
      </div>
      <div className="relative grid grid-cols-3 border-t border-white/15 bg-black/20 text-center"><div className="p-4"><p className="text-2xl font-black">25</p><p className="text-xs text-white/60">Review slides</p></div><div className="border-x border-white/10 p-4"><p className="text-2xl font-black">3</p><p className="text-xs text-white/60">Group members</p></div><div className="p-4"><p className="text-2xl font-black">2026</p><p className="text-xs text-white/60">Fall course</p></div></div>
    </section>

    <section aria-label="Original presentation resources" className="grid gap-4 sm:grid-cols-3">
      <a href={PRESENTATION_FOLDER} target="_blank" rel="noopener noreferrer" className="rounded-2xl border border-line bg-surface-muted p-5 transition hover:border-accent/50 hover:shadow-lg"><p className="text-xs font-bold uppercase tracking-widest text-accent">Source artifact</p><h2 className="mt-2 text-lg font-bold">Original PowerPoint ↗</h2><p className="mt-2 text-sm text-ink-muted">Open the shared presentation folder. File access follows Google Drive sharing settings.</p></a>
      <a href="#slide-explorer" className="rounded-2xl border border-line bg-surface-muted p-5 transition hover:border-accent/50 hover:shadow-lg"><p className="text-xs font-bold uppercase tracking-widest text-accent">Read & present</p><h2 className="mt-2 text-lg font-bold">Interactive slide explorer</h2><p className="mt-2 text-sm text-ink-muted">Browse our reviewed 25-slide research narrative, organized into six chapters.</p></a>
      <Link href="/reference-paper" className="rounded-2xl border border-line bg-surface-muted p-5 transition hover:border-accent/50 hover:shadow-lg"><p className="text-xs font-bold uppercase tracking-widest text-accent">Scientific reference</p><h2 className="mt-2 text-lg font-bold">Published reference paper ↗</h2><p className="mt-2 text-sm text-ink-muted">Inspect the original study independently of our follow-up project.</p></Link>
    </section>

    <PresentationOneViewer />

    <section aria-labelledby="research-boundary" className="rounded-2xl border border-line bg-surface-muted p-6 sm:p-8">
      <p className="text-xs font-bold uppercase tracking-[.16em] text-accent">Academic integrity</p>
      <h2 id="research-boundary" className="mt-2 text-2xl font-bold">Published evidence versus our research</h2>
      <p className="mt-3 max-w-4xl leading-relaxed text-ink-muted">Reported model results in Presentation 1 come from Ismail, Dandan and Qushou (2025). Our own streaming prototypes, synthetic demonstrations and planned follow-up measurements must not be mistaken for independent reproduction of those benchmark results. Original slide speaker assignments require team review.</p>
      <div className="mt-5 flex flex-wrap gap-3"><a href="https://doi.org/10.1109/ACCESS.2025.3554083" target="_blank" rel="noopener noreferrer" className="rounded-xl border border-line px-4 py-2 text-sm font-semibold">Reference DOI ↗</a><Link href="/course" className="rounded-xl bg-[#1b507d] px-4 py-2 text-sm font-semibold text-white">Continue to our Presentation 2</Link></div>
      <p className="mt-4 text-xs text-ink-muted">Original source deck: Grad1_Final_Presentation_Arun_Updated.pptx (October 7, 2026). This page is a guided text adaptation, not an exact visual reproduction of the PPTX.</p>
    </section>
  </div>;
}
