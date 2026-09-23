import type { Metadata } from "next";

import { PageHeader, Planned } from "@/components/ui";

export const metadata: Metadata = { title: "Model Explorer" };

export default function ModelExplorerPage() {
  return (
    <>
      <PageHeader
        title="Model Explorer"
        lede="Per-model metrics, measured resource costs, and published model versions."
        milestone="M6–M8"
      />
      <Planned milestone="M6–M8">
        <p>
          Accuracy, per-class recall and calibration alongside measured model size, peak memory,
          p50/p95/p99 latency and throughput, with a link to each evaluated artifact&rsquo;s model
          card. A validated inference form will call the API boundary described on the
          Architecture page.
        </p>
      </Planned>
    </>
  );
}
