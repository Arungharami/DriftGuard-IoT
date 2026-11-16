"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const primary = [
  {href:"/", label:"Overview"},
  {href:"/presentation-1", label:"Presentation 1"},
  {href:"/presentation-2", label:"Presentation 2"},
  {href:"/paper", label:"Paper"},
  {href:"/research", label:"Research"}
];
const explore = [
  {href:"/architecture",label:"Architecture",desc:"MQTT and edge pipeline"},
  {href:"/datasets",label:"Datasets",desc:"Sources and provenance"},
  {href:"/experiments",label:"Experiments",desc:"Evidence and evaluation"},
  {href:"/drift-lab",label:"Drift Lab",desc:"Explore drift behavior"},
  {href:"/model-explorer",label:"Model Explorer",desc:"Model comparisons"},
  {href:"/demo",label:"Live Demo",desc:"Synthetic telemetry"},
  {href:"/reproducibility",label:"Reproducibility",desc:"Protocols and artifacts"},
  {href:"/project-history",label:"Our Journey",desc:"Research milestones"},
  {href:"/team",label:"Team",desc:"People and instructor"},
  {href:"/resources",label:"Resources",desc:"Source material"},
  {href:"/related-research",label:"Related Research",desc:"Literature and context"},
  {href:"/reference-paper",label:"Reference Paper",desc:"Original study"},
  {href:"/contribution",label:"Our Contribution",desc:"Research objectives"},
  {href:"/cross-domain",label:"Cross-Domain",desc:"Transfer evaluation"},
  {href:"/robustness",label:"Robustness",desc:"Stability analysis"},
  {href:"/explainability",label:"Explainability",desc:"Model explanations"},
  {href:"/publications",label:"Publications",desc:"Scholarly materials"}
];
export function NavLinks({orientation}:{orientation:"horizontal"|"vertical"}){
  const pathname=usePathname();
  const mobile=orientation==="vertical";
  const link=(p:{href:string;label:string})=>{
    const active=p.href==="/" ? pathname==="/" : pathname===p.href;
    return <Link key={p.href} href={p.href} aria-current={active?"page":undefined} className={`block rounded-full px-3.5 py-2 text-sm transition-colors ${active?"bg-[#214a69] font-semibold text-white":"text-ink-muted hover:bg-surface-muted hover:text-ink"}`}>{p.label}</Link>;
  };
  return <div className={mobile?"flex flex-col gap-1":"flex items-center gap-1"}>
    {primary.map(link)}
    <details className={mobile?"group":"group relative"}>
      <summary className="cursor-pointer list-none rounded-full px-3.5 py-2 text-sm text-ink-muted marker:hidden hover:bg-surface-muted hover:text-ink focus-visible:outline">Explore <span className="inline-block text-xs transition group-open:rotate-180">⌄</span></summary>
      <div className={mobile?"mt-2 grid grid-cols-1 gap-1 border-t border-line pt-2":"absolute right-0 top-full z-50 mt-2 grid w-[480px] grid-cols-2 gap-1 rounded-2xl border border-line bg-surface p-3 shadow-2xl"}>
        {explore.map((p)=><Link key={p.href} href={p.href} className="rounded-xl px-3 py-2 transition hover:bg-surface-muted"><span className="block text-sm font-semibold">{p.label}</span><span className="mt-0.5 block text-xs text-ink-muted">{p.desc}</span></Link>)}
      </div>
    </details>
  </div>;
}
