import Link from "next/link";
import { PORTRAITS } from "@/content/portraits";
import { PersonPortrait } from "./PersonPortrait";

const people = [
  {name: "Professor Mohammad Ilyas", role: "CNT 6167 · Course Instructor", url: "https://www.fau.edu/engineering/directory/faculty/ilyas/"},
  {name: "Arun Kumar Gharami", role: "Grad1 · Co-presenter", url: "https://huggingface.co/arun-gharami"},
  {name: "Ankith Gajam", role: "Grad1 · Co-presenter", url: "https://www.linkedin.com/in/ankithgajam/"},
];

export function TeamPortraits() {
  return (
    <section className="mb-14 scroll-mt-24" aria-labelledby="people-title">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[.16em] text-accent">People & guidance</p>
          <h2 id="people-title" className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">The people behind our project</h2>
          <p className="mt-2 text-sm text-ink-muted">Presentation 2 · Two Grad1 co-presenters and our CNT 6167 course instructor.</p>
        </div>
        <Link href="/team" className="rounded-full border border-line px-4 py-2 text-sm font-semibold transition hover:border-accent hover:text-accent">Meet our team ↗</Link>
      </div>
      <ul className="grid gap-3 sm:grid-cols-3">
        {people.map((person) => (
          <li key={person.name} className="rounded-2xl border border-line bg-surface-muted/60 p-3.5 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/50 hover:shadow-md">
            <div className="flex items-center gap-3">
              <div className="w-[76px] shrink-0 [&>div]:mb-0 [&>div]:rounded-xl">
                <PersonPortrait name={person.name} src={PORTRAITS[person.name]?.src} />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold leading-snug">{person.name}</h3>
                <p className="mt-1 text-xs text-ink-muted">{person.role}</p>
                <a href={person.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs font-medium text-accent underline underline-offset-4">Public profile ↗</a>
              </div>
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-ink-muted">Professor Ilyas is the course instructor, not a student team member. Presentation 1 retains its original team credits in the archived review.</p>
    </section>
  );
}
