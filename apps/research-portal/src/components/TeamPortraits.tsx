import Link from "next/link";
import { TEAM } from "@/content/site";
import { PORTRAITS } from "@/content/portraits";
import { PersonPortrait } from "./PersonPortrait";

export function TeamPortraits() {
  const people = [
    ...TEAM.map((person) => ({ name: person.name, role: "Original Grad1 team" })),
    { name: "Professor Mohammad Ilyas", role: "CNT 6167 instructor" },
  ];
  return (
    <section className="mb-14 scroll-mt-24" aria-labelledby="people-title">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[.16em] text-accent">Researchers and guidance</p>
          <h2 id="people-title" className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">The people behind our project</h2>
          <p className="mt-2 text-sm text-ink-muted">Our original Grad1 group and course instructor. Presentation 2 features Arun and Ankith.</p>
        </div>
        <Link href="/team" className="rounded-full border border-line px-4 py-2 text-sm font-semibold transition hover:border-accent hover:text-accent">Meet our team ↗</Link>
      </div>
      <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {people.map((person) => (
          <li key={person.name} className="min-w-0 rounded-2xl border border-line bg-surface-muted/60 p-3.5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/50 hover:shadow-md">
            <div className="flex items-center gap-3">
              <div className="w-16 shrink-0 [&>div]:mb-0 [&>div]:rounded-xl sm:w-[72px]">
                <PersonPortrait name={person.name} src={PORTRAITS[person.name]?.src} />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold leading-snug">{person.name}</h3>
                <p className="mt-1 text-xs text-ink-muted">{person.role}</p>
                {PORTRAITS[person.name] ? (
                  <a href={PORTRAITS[person.name]!.source} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs font-medium text-accent underline underline-offset-4">Photo source ↗</a>
                ) : <span className="mt-2 inline-block text-xs text-ink-muted">Photo pending</span>}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
