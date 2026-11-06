import type { Metadata } from "next";
import Link from "next/link";

import { Card, PageHeader, Section, StatusBadge } from "@/components/ui";
import { REFERENCE_PAPER } from "@/content/site";

export const metadata: Metadata = { title: "Publications" };

export default function PublicationsPage() {
  return (
    <>
      <PageHeader
        title="Publications & research outputs"
        lede="Project manuscripts, source papers, and companion research with transparent evidence status."
      />
      <Section title="DriftGuard-IoT">
        <Card title="DriftGuard-IoT: Drift-Aware, Delayed-Label Intrusion Detection for Resource-Constrained IoT Edge Gateways">
          <p>
            <StatusBadge kind="simulated" label="Controlled simulation · synthetic flows" />
          </p>
          <p>
            A. K. Gharami, S. Rabbany and A. Gajam. CNT 6167 Internet of Things group research
            paper, Florida Atlantic University, 2026. About 5,500 words, six figures, four
            tables and 22 references.
          </p>
          <p>
            <Link className="underline underline-offset-4" href="/paper">
              Read the paper with interactive figures
            </Link>{" "}
            or switch to the classic paper view to print it.
          </p>
        </Card>
        <p className="text-sm text-ink-muted">
          The full TON_IoT, WUSTL-IIoT-2021 and Edge-IIoTset manuscript remains planned for
          milestone M10. The repository currently reports M2 development status; synthetic
          and development runs are not reportable research results.
        </p>
      </Section>

      <Section title="Related research">
        <Card title="DriftCVE-NLP — temporal CVE-to-CWE classification and vulnerability retrieval">
          <p className="text-sm leading-6 text-ink-muted">
            A companion NLP project that studies whether vulnerability classifiers and
            retrievers remain reliable as CVE language and label distributions change over
            time. Its portal includes a working-draft paper, dataset protocol, classification
            and retrieval analyses, drift diagnostics, error examples, and reproduction
            instructions.
          </p>
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <Link className="font-medium text-accent underline underline-offset-4" href="/related-research">
              Open research deep dive
            </Link>
            <a className="underline underline-offset-4" href="https://driftcve-nlp.vercel.app/">
              Open DriftCVE-NLP portal ↗
            </a>
            <a className="underline underline-offset-4" href="https://driftcve-nlp.vercel.app/paper/driftcve.pdf">
              Read working-draft PDF ↗
            </a>
          </div>
        </Card>
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
