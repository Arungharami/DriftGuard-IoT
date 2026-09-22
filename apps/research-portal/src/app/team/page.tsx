import type { Metadata } from "next";

import { PageHeader } from "@/components/ui";
import { REPO_URL, TEAM } from "@/content/site";

export const metadata: Metadata = { title: "Team" };

export default function TeamPage() {
  return (
    <>
      <PageHeader title="Team" lede="People behind DriftGuard-IoT." />
      <ul className="mb-8 grid gap-4 sm:grid-cols-3">
        {TEAM.map((member) => (
          <li key={member.name} className="rounded-lg border border-line p-5">
            <p className="font-semibold">{member.name}</p>
            <p className="mt-1 text-sm text-ink-muted">{member.affiliation}</p>
          </li>
        ))}
      </ul>
      <p className="text-sm text-ink-muted">
        Individual roles will be listed once agreed by the team. Contributions are tracked in
        the{" "}
        <a className="underline" href={REPO_URL}>
          repository
        </a>
        .
      </p>
    </>
  );
}
