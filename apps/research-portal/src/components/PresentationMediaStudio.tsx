"use client";

import { useState } from "react";

const SLIDES_URL = "https://docs.google.com/presentation/d/1LTQs5JwvnbwJjxSYeeAMVchC1KtSeYXUo8eW5Hakgmo/edit?usp=drivesdk";
const EMBED_URL = "https://docs.google.com/presentation/d/1LTQs5JwvnbwJjxSYeeAMVchC1KtSeYXUo8eW5Hakgmo/embed?start=false&loop=false&delayms=3000";

export function PresentationMediaStudio() {
  const [active, setActive] = useState<"slides" | "video">("slides");
  return (
    <section id="media-studio" aria-labelledby="studio-title" className="scroll-mt-28 space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[.16em] text-accent">Watch & present</p>
          <h2 id="studio-title" className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">Presentation media studio</h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">A dedicated presentation player and slide viewer, based on our Biomedical Hybrid IR course-page layout.</p>
        </div>
        <div className="flex gap-2 rounded-xl border border-line bg-surface-muted p-1" role="tablist" aria-label="Presentation media">
          <button role="tab" id="tab-slides" aria-controls="panel-slides" aria-selected={active === "slides"} onClick={() => setActive("slides")} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${active === "slides" ? "bg-[#173d60] text-white shadow" : "text-ink-muted hover:text-ink"}`}>Slides · 21</button>
          <button role="tab" id="tab-video" aria-controls="panel-video" aria-selected={active === "video"} onClick={() => setActive("video")} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${active === "video" ? "bg-[#173d60] text-white shadow" : "text-ink-muted hover:text-ink"}`}>Video</button>
        </div>
      </div>
      <div className="overflow-hidden rounded-2xl border border-line bg-surface-muted shadow-xl shadow-black/10">
        {active === "slides" ? (
          <div id="panel-slides" role="tabpanel" aria-labelledby="tab-slides" className="grid gap-0 lg:grid-cols-[minmax(0,1.7fr)_minmax(250px,.8fr)]">
            <div className="relative min-h-[260px] bg-[#07152b] sm:min-h-[360px]">
              <iframe title="DriftGuard-IoT Presentation 2, 21 slide deck" src={EMBED_URL} loading="lazy" allowFullScreen className="absolute inset-0 h-full w-full border-0" referrerPolicy="strict-origin-when-cross-origin"/>
            </div>
            <aside className="flex flex-col justify-center gap-3 p-5 sm:p-7">
              <span className="w-fit rounded-full border border-line px-3 py-1 text-xs font-semibold text-ink-muted">Google Slides · 21 slides</span>
              <h3 className="text-xl font-bold">DriftGuard-IoT · Presentation 2</h3>
              <p className="text-sm leading-relaxed text-ink-muted">Arun Kumar Gharami & Ankith Gajam · Professor Mohammad Ilyas · CNT 6167, Fall 2026.</p>
              <p className="text-xs leading-relaxed text-ink-muted">Google Slides visibility is controlled by the deck owner's sharing settings. If the embedded viewer requests access, open the original deck or ask the owner to enable viewer access.</p>
              <a href={SLIDES_URL} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#1b507d] px-5 py-2 text-sm font-semibold text-white transition hover:bg-[#286696]">Open full slide deck ↗</a>
              <a href="/paper" className="inline-flex min-h-11 items-center justify-center rounded-xl border border-line px-5 py-2 text-sm font-semibold">Read full research paper</a>
            </aside>
          </div>
        ) : (
          <div id="panel-video" role="tabpanel" aria-labelledby="tab-video" className="grid lg:grid-cols-[minmax(0,1.7fr)_minmax(250px,.8fr)]">
            <div className="relative flex aspect-video items-center justify-center overflow-hidden bg-gradient-to-br from-[#143a60] via-[#07152b] to-[#1c1833] p-8 text-center">
              <div className="absolute inset-0 opacity-[.08]" style={{backgroundImage:"linear-gradient(white 1px,transparent 1px),linear-gradient(90deg,white 1px,transparent 1px)",backgroundSize:"38px 38px"}}/>
              <div className="relative space-y-4">
                <span aria-hidden="true" className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-white/30 bg-white/10 text-3xl text-white">▶</span>
                <h3 className="text-xl font-bold text-white">Presentation 2 video</h3>
                <p className="max-w-md text-sm text-white/70">Video upload pending. The site does not claim an unpublished recording is available.</p>
              </div>
            </div>
            <aside className="flex flex-col justify-center gap-3 p-5 sm:p-7">
              <span className="w-fit rounded-full border border-line px-3 py-1 text-xs font-semibold">Media pending</span>
              <h3 className="text-xl font-semibold">10-minute academic research overview</h3>
              <p className="text-sm leading-relaxed text-ink-muted">Once an approved MP4 is hosted, this panel will support native playback, captions and chapter navigation. For now, explore the slide presentation and full paper.</p>
              <button onClick={() => setActive("slides")} className="min-h-11 rounded-xl bg-[#1b507d] px-5 py-2 text-sm font-semibold text-white hover:bg-[#286696]">View presentation slides</button>
            </aside>
          </div>
        )}
      </div>
    </section>
  );
}
