import type { Metadata } from "next";

import Link from "next/link";

import { Card, PageHeader, Section, StatusBadge } from "@/components/ui";
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
        <Card title="DriftGuard-IoT: Drift-Aware, Delayed-Label Intrusion Detection for Resource-Constrained IoT Edge Gateways">
          <p>
            <StatusBadge kind="simulated" label="Controlled simulation · synthetic flows" />
          </p>
          <p>
            A. K. Gharami, S. Rabbany and A. Gajam. CNT 6167 Internet of Things group research paper, Florida
            Atlantic University, 2026. About 5,500 words, six figures, four tables and 22 references.
          </p>
          <p>
            <Link className="underline" href="/paper">
              Read the paper with interactive figures
            </Link>{" "}
            or switch to the classic paper view to print it.
          </p>
        </Card>
        <p className="text-sm text-ink-muted">
          The full TON_IoT, WUSTL-IIoT-2021 and Edge-IIoTset manuscript remains planned for milestone M10.
        </p>
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
