"use client";

import { useState } from "react";
import { SLIDE_REVIEW } from "@/content/group";

const chapters = [
  { name: "Introduction & motivation", from: 0, to: 5 },
  { name: "Architecture & methodology", from: 6, to: 9 },
  { name: "Published paper results", from: 10, to: 14 },
  { name: "Critical review", from: 15, to: 16 },
  { name: "Our project & proposed research", from: 17, to: 22 },
  { name: "Conclusion & references", from: 23, to: 24 },
];

export function PresentationOneViewer() {
  const [active, setActive] = useState(0);
  const slide = SLIDE_REVIEW[active] ?? SLIDE_REVIEW[0];
  const chapter = chapters.find((c) => active >= c.from && active <= c.to);
  if (!slide) return null;
  const changeSlide = (next: number) => setActive(Math.max(0, Math.min(SLIDE_REVIEW.length - 1, next)));
  return (
    <section id="slide-explorer" aria-labelledby="slide-explorer-title" className="scroll-mt-28 space-y-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[.2em] text-accent">25-slide interactive study companion</p>
        <h2 id="slide-explorer-title" className="mt-2 text-2xl font-bold sm:text-3xl">Presentation 1 · Slide explorer</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">Browse the research narrative in a lecture-friendly slide interface. This is a structured companion to the original PowerPoint, not a screenshot or substitute for its precise figures and original visual design.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.65fr)_minmax(260px,.65fr)]">
        <div className="overflow-hidden rounded-2xl border border-[#365d84] bg-[#081a32] shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/15 px-5 py-3">
            <span className="text-xs font-semibold uppercase tracking-[.15em] text-sky-200">CNT 6167 · Grad1 · FAU</span>
            <span className="rounded-full border border-white/20 px-3 py-1 text-xs text-white/70">Slide {active + 1} / {SLIDE_REVIEW.length}</span>
          </div>
          <div className="relative flex min-h-[310px] flex-col justify-center bg-gradient-to-br from-[#123b69] via-[#0a2746] to-[#08152c] px-7 py-10 sm:min-h-[420px] sm:px-12">
            <div className="pointer-events-none absolute -right-8 -top-10 text-[170px] font-black leading-none text-white/[.035]">{String(active + 1).padStart(2,"0")}</div>
            <div className="relative">
              <p className="text-xs font-bold uppercase tracking-[.19em] text-[#9edced]">{chapter?.name ?? "Research presentation"}</p>
              <h3 className="mt-5 max-w-2xl text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl">{slide[0]}</h3>
              <div className="mt-7 h-1 w-20 rounded-full bg-[#e65a6c]"/>
              <p className="mt-7 max-w-2xl text-base leading-relaxed text-[#d8e8f4] sm:text-lg">{slide[1]}</p>
            </div>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-white/15 px-4 py-4 sm:px-6">
            <button type="button" onClick={() => changeSlide(active - 1)} disabled={active===0} className="min-h-11 rounded-xl border border-white/30 px-5 text-sm font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-35">← Previous</button>
            <div className="hidden h-1.5 flex-1 overflow-hidden rounded-full bg-white/15 sm:block" aria-hidden="true"><div className="h-full rounded-full bg-sky-300 transition-all" style={{width:`${((active+1)/SLIDE_REVIEW.length)*100}%`}}/></div>
            <button type="button" onClick={() => changeSlide(active + 1)} disabled={active===SLIDE_REVIEW.length-1} className="min-h-11 rounded-xl bg-white px-5 text-sm font-semibold text-[#092743] transition hover:bg-[#d5eaf6] disabled:cursor-not-allowed disabled:opacity-35">Next →</button>
          </div>
        </div>
        <aside aria-label="Presentation slide chapters" className="rounded-2xl border border-line bg-surface-muted p-5">
          <h3 className="font-bold">Presentation chapters</h3>
          <p className="mt-1 text-xs text-ink-muted">Jump to a section or select any slide below.</p>
          <div className="mt-4 space-y-2">
            {chapters.map((c,i)=><button type="button" key={c.name} onClick={()=>changeSlide(c.from)} aria-current={active>=c.from&&active<=c.to?"step":undefined} className={`block w-full rounded-lg border px-3 py-3 text-left transition ${active>=c.from&&active<=c.to?"border-[#5f9fcb] bg-[#143956] text-white":"border-line hover:border-accent"}`}>
              <span className="block text-[10px] font-semibold uppercase tracking-widest opacity-70">Part {String(i+1).padStart(2,"0")} · Slides {c.from+1}–{c.to+1}</span>
              <span className="mt-1 block text-sm font-semibold">{c.name}</span>
            </button>)}
          </div>
        </aside>
      </div>
      <div className="space-y-4">
        <h3 className="text-xl font-bold">All 25 slides</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {SLIDE_REVIEW.map(([title],i)=><button key={i} type="button" onClick={()=>{changeSlide(i); document.getElementById("slide-explorer")?.scrollIntoView({behavior:"smooth",block:"start"});}} aria-current={active===i?"step":undefined} className={`flex min-h-16 items-center gap-3 rounded-xl border p-3 text-left transition ${active===i?"border-[#4c8ab7] bg-[#163c60] text-white":"border-line bg-surface-muted hover:border-accent"}`}>
            <span className="shrink-0 text-xs font-bold tabular-nums opacity-70">{String(i+1).padStart(2,"0")}</span>
            <span className="text-sm font-semibold leading-snug">{title}</span>
          </button>)}
        </div>
      </div>
    </section>
  );
}
