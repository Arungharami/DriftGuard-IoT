import Link from "next/link";
import { TEAM } from "@/content/site";
import { PORTRAITS } from "@/content/portraits";
import { PersonPortrait } from "./PersonPortrait";

export function TeamPortraits() {
  const people = [...TEAM.map((person) => ({ name: person.name, role: "Grad1 team member" })), { name: "Professor Mohammad Ilyas", role: "CNT 6167 course instructor" }];
  return <section className="mb-12" aria-labelledby="people-title">
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 id="people-title" className="text-xl font-semibold">The people behind our project</h2><Link href="/team" className="text-sm underline underline-offset-4">Meet Grad1 and our instructor</Link></div>
    <ul className="grid grid-cols-2 gap-4 sm:grid-cols-4">{people.map((person) => <li key={person.name} className="min-w-0 rounded-xl border border-line p-3"><PersonPortrait name={person.name} src={PORTRAITS[person.name]?.src} /><h3 className="text-sm font-semibold">{person.name}</h3><p className="mt-1 text-xs text-ink-muted">{person.role}</p>{PORTRAITS[person.name] ? <a href={PORTRAITS[person.name]!.source} className="mt-3 inline-block text-xs text-ink-muted underline underline-offset-4">Photo source</a> : null}</li>)}</ul>
  </section>;
}
