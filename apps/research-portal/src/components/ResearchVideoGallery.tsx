"use client";

import { useState } from "react";

const videos = [
  { id:"13HCnHc8nN0xsd_7qJVsQTuLmMZSoa5RC", title:"DriftGuard-IoT Security", label:"Research presentation", description:"Main DriftGuard-IoT security research video." },
  { id:"1SPA-AP95OMPeIpNOYkAZnpBKQRbjO0ew", title:"How IoT Security Models Forget to Learn", label:"Concept explainer", description:"Illustrated explanation of changing IoT traffic, model drift and adaptation." },
];

export function ResearchVideoGallery() {
  const [selected,setSelected] = useState(0);
  const active = videos[selected];
  return <div className="space-y-4">
    <div className="grid gap-3 sm:grid-cols-2" role="tablist" aria-label="Choose a research video">
      {videos.map((video,i)=><button key={video.id} type="button" role="tab" aria-selected={selected===i} aria-controls="driftguard-video-panel" onClick={()=>setSelected(i)} className={`rounded-2xl border p-4 text-left transition ${selected===i?"border-accent bg-surface-muted ring-2 ring-accent/25":"border-line hover:border-accent/50"}`}>
        <span className="block text-[11px] font-bold uppercase tracking-widest text-accent">0{i+1} · {video.label}</span><span className="mt-1 block text-base font-semibold">{video.title}</span><span className="mt-2 block text-xs text-ink-muted">{video.description}</span>
      </button>)}
    </div>
    <div id="driftguard-video-panel" role="tabpanel" className="grid overflow-hidden rounded-2xl border border-line bg-surface-muted shadow-xl lg:grid-cols-[minmax(0,1.6fr)_minmax(240px,.7fr)]">
      <div className="relative aspect-video bg-[#07152b]"><iframe key={active.id} src={`https://drive.google.com/file/d/${active.id}/preview`} className="absolute inset-0 h-full w-full border-0" title={active.title} loading="lazy" allow="autoplay; fullscreen; encrypted-media" allowFullScreen referrerPolicy="strict-origin-when-cross-origin"/></div>
      <aside className="flex flex-col justify-center gap-3 p-5">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-accent">{active.label}</p>
        <h3 className="text-xl font-bold">{active.title}</h3>
        <p className="text-sm leading-relaxed text-ink-muted">{active.description}</p>
        <p className="text-xs leading-relaxed text-ink-muted">Playback is embedded from Google Drive. It requires access to the source file; if you see an access request, the owner must enable “Anyone with the link — Viewer.” The video is not yet hosted on Vercel.</p>
        <a href={`https://drive.google.com/file/d/${active.id}/view`} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#1b507d] px-4 py-2 text-sm font-semibold text-white hover:bg-[#286696]">Open original recording ↗</a>
      </aside>
    </div>
  </div>;
}
