import type { Metadata } from "next";

import { PageHeader, Planned, StatusBadge } from "@/components/ui";

export const metadata: Metadata = { title: "Drift Lab" };

export default function DriftLabPage() {
  return (
    <>
      <PageHeader
        title="Drift Lab"
        lede="An interactive demonstration of drift monitoring on labelled synthetic or approved example traffic."
        milestone="M8"
      />
      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-line p-4 text-sm">
        <StatusBadge kind="simulated" />
        <p className="text-ink-muted">
          Everything in the Drift Lab is a simulation. It is visually and structurally separate
          from recorded research results and never feeds the Experiments dashboard.
        </p>
      </div>
      <Planned milestone="M5 (method) and M8 (interactive demo)">
        <p>
          Feature-drift statistics (for example PSI and two-sample Kolmogorov–Smirnov) over a
          sliding window, alert thresholds calibrated on training/validation data only, and a
          side-by-side view of the no-adaptation baseline, periodic retraining and the
          drift-triggered policy.
        </p>
      </Planned>
    </>
  );
}
