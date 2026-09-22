import type { Metadata } from "next";

import { PageHeader, Planned } from "@/components/ui";

export const metadata: Metadata = { title: "Explainability" };

export default function ExplainabilityPage() {
  return (
    <>
      <PageHeader
        title="Explainability"
        lede="Global feature importance and feature-selection stability across datasets and splits."
        milestone="M6"
      />
      <Planned milestone="M6">
        <p>
          Optional SHAP summaries for supported models, mutual-information rankings and
          selection-stability scores across resamples and environments.
        </p>
        <p>
          Public explanations exclude private or potentially identifying source features such
          as IP addresses, MAC addresses and raw payload-derived fields.
        </p>
      </Planned>
    </>
  );
}
