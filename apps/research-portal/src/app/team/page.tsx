import type { Metadata } from "next";

import Link from "next/link";
import { PersonPortrait } from "@/components/PersonPortrait";
import { PORTRAITS } from "@/content/portraits";
import { PageHeader, Section } from "@/components/ui";
import { REPO_URL } from "@/content/site";

export const metadata: Metadata = { title: "Team" };

export default function TeamPage() {
  return (
    <>
      <PageHeader title="The People Behind Our Project" lede="Presentation 2 · DriftGuard-IoT · CNT 6167 · Florida Atlantic University." />
      <ul className="mb-5 grid gap-4 sm:grid-cols-3">
        {[
          {name: "Professor Mohammad Ilyas", role: "CNT 6167 Course Instructor", link: "https://www.fau.edu/engineering/directory/faculty/ilyas/"},
          {name: "Arun Kumar Gharami", role: "Grad1 · Co-presenter", link: "https://huggingface.co/arun-gharami"},
          {name: "Ankith Gajam", role: "Grad1 · Co-presenter", link: "https://www.linkedin.com/in/ankithgajam/"},
        ].map((member) => (
          <li key={member.name} className="rounded-2xl border border-line bg-surface-muted p-4">
            <div className="flex items-center gap-3">
              <div className="w-[88px] shrink-0 [&>div]:mb-0"><PersonPortrait name={member.name} src={PORTRAITS[member.name]?.src} /></div>
              <div className="min-w-0">
                <h2 className="font-semibold leading-snug">{member.name}</h2>
                <p className="mt-1 text-xs text-ink-muted">{member.role}</p>
                <a href={member.link} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-xs font-medium text-accent underline">Public profile ↗</a>
              </div>
            </div>
          </li>
        ))}
      </ul>
      <p className="mb-10 text-xs text-ink-muted">These are the original photographs supplied for Presentation 2. Professor Ilyas is the instructor, not a student team member. The original Presentation 1 group membership and credits remain documented in the archived slide review.</p>
      <Section title="Professor Mohammad Ilyas">
        <div className="rounded-xl border border-line bg-surface-muted p-6 sm:p-8">
          <div className="max-w-48"><PersonPortrait name="Professor Mohammad Ilyas" src={PORTRAITS["Professor Mohammad Ilyas"]!.src} /></div>
          <p className="text-sm font-medium text-accent">Course instructor / CNT 6167</p>
          <p className="mt-3 max-w-3xl leading-relaxed text-ink-muted">Professor Ilyas is a professor in FAU’s Department of Electrical Engineering and Computer Science. His research interests include wireless communication networks, sensor networks and smart systems, and network performance modeling.</p>
          <p className="mt-4 max-w-3xl leading-relaxed text-ink-muted">We thank Professor Ilyas for approving our reference paper for Presentation 1 and encouraging us to move forward. His course provided the setting for our group’s review and motivated us to examine how detection models behave under real IoT constraints.</p>
          <a className="mt-5 inline-block text-sm underline underline-offset-4" href="https://www.fau.edu/engineering/directory/faculty/ilyas/">Official FAU faculty profile</a>
          <p className="mt-4 text-sm text-ink-muted">This acknowledgment describes course guidance. Research responsibilities and authorship will be agreed separately.</p>
        </div>
      </Section>
      <p id="portrait-credits" className="mb-8 text-xs text-ink-muted">Presentation 2 profile photos are the original images uploaded by the project team. Professor Ilyas is credited as CNT 6167 instructor; Arun and Ankith are the two co-presenters.</p>
      <Section title="How we coordinate our work">
        <p className="max-w-3xl text-ink-muted">We can use repository issues to agree on tasks, attach evidence and request review. The history page records development milestones, while Presentation 1 gives everyone a common review point. New roles, photos and credits should reflect the team’s agreement.</p>
        <div className="flex flex-wrap gap-5 text-sm"><a className="underline underline-offset-4" href={`${REPO_URL}/issues`}>View project tasks</a><Link className="underline underline-offset-4" href="/project-history">Read our journey</Link><Link className="underline underline-offset-4" href="/presentation-1">Review Presentation 1</Link></div>
      </Section>
    </>
  );
}
