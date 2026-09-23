import type { Metadata } from "next";

import { Card, PageHeader, Section } from "@/components/ui";
import { REFERENCE_PAPER } from "@/content/site";

export const metadata: Metadata = { title: "Publications" };

export default function PublicationsPage() {
  return (
    <>
      <PageHeader
        title="Publications"
        lede="Project outputs and the reference work they build on."
      />
      <Section title="Project publications">
        <p className="text-ink-muted">None yet. A manuscript is planned for milestone M10.</p>
      </Section>
      <Section title="Reference work">
        <Card title="Reproduced and extended study">
          <p>{REFERENCE_PAPER.citation}</p>
          <p>
            <a className="underline" href={`https://doi.org/${REFERENCE_PAPER.doi}`}>
              doi:{REFERENCE_PAPER.doi}
            </a>
          </p>
        </Card>
      </Section>
    </>
  );
}
