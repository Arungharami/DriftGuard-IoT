import type { Metadata } from "next";

import Link from "next/link";
import { PageHeader, Section } from "@/components/ui";
import { REPO_URL, TEAM } from "@/content/site";

export const metadata: Metadata = { title: "Team" };

export default function TeamPage() {
  return (
    <>
      <PageHeader title="Meet Grad1" lede="Three course teammates developing a shared understanding of IoT security through paper review and reproducible research." />
      <ul className="mb-8 grid gap-4 sm:grid-cols-3">
        {TEAM.map((member) => (
          <li key={member.name} className="rounded-lg border border-line p-5">
            <div aria-hidden="true" className="mb-5 flex h-20 w-20 items-center justify-center rounded-full border border-line bg-surface-muted text-2xl font-semibold text-accent">{member.name.split(" ").map((part) => part[0]).join("")}</div>
            <p className="font-semibold">{member.name}</p>
            <p className="mt-1 text-sm text-ink-muted">{member.affiliation}</p>
            <p className="mt-4 text-sm leading-relaxed text-ink-muted">{member.name === "Arun Kumar Gharami" ? "Team member. Presentation 1 includes Arun’s DriftGuard-IoT implementation update and proposed evaluation plan." : "Team member and co-presenter in Presentation 1, contributing to our shared review of lightweight IoT intrusion detection."}</p>
          </li>
        ))}
      </ul>
      <p className="mb-10 text-sm text-ink-muted">
        Initials stand in for portraits until approved photos are supplied. Names follow our existing deck.
        Detailed biographies and individual research roles will be added after team review. Contributions are tracked in
        the{" "}
        <a className="underline" href={REPO_URL}>
          repository
        </a>
        .
      </p>
      <Section title="Professor Mohammad Ilyas">
        <div className="rounded-xl border border-line bg-surface-muted p-6 sm:p-8">
          <p className="text-sm font-medium text-accent">Course instructor / CNT 6167</p>
          <p className="mt-3 max-w-3xl leading-relaxed text-ink-muted">Professor Ilyas is a professor in FAU’s Department of Electrical Engineering and Computer Science. His research interests include wireless communication networks, sensor networks and smart systems, and network performance modeling.</p>
          <p className="mt-4 max-w-3xl leading-relaxed text-ink-muted">We thank Professor Ilyas for approving our reference paper for Presentation 1 and encouraging us to move forward. His course provided the setting for our group’s review and motivated us to examine how detection models behave under real IoT constraints.</p>
          <a className="mt-5 inline-block text-sm underline underline-offset-4" href="https://www.fau.edu/engineering/directory/faculty/ilyas/">Official FAU faculty profile</a>
          <p className="mt-4 text-sm text-ink-muted">This acknowledgment describes course guidance. Research responsibilities and authorship will be agreed separately.</p>
        </div>
      </Section>
      <Section title="How we coordinate our work">
        <p className="max-w-3xl text-ink-muted">We can use repository issues to agree on tasks, attach evidence and request review. The history page records development milestones, while Presentation 1 gives everyone a common review point. New roles, photos and credits should reflect the team’s agreement.</p>
        <div className="flex flex-wrap gap-5 text-sm"><a className="underline underline-offset-4" href={`${REPO_URL}/issues`}>View project tasks</a><Link className="underline underline-offset-4" href="/project-history">Read our journey</Link><Link className="underline underline-offset-4" href="/presentation-1">Review Presentation 1</Link></div>
      </Section>
    </>
  );
}
