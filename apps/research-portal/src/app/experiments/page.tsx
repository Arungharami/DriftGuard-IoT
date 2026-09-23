import type { Metadata } from "next";

import { ResultsExplorer } from "@/components/ResultsExplorer";
import { M5Readiness } from "@/components/M5Readiness";
import { ResultsChart } from "@/components/ResultsChart";
import { PageHeader, Section, StatusBadge } from "@/components/ui";
import { resultsIndex } from "@/lib/results";

export const metadata: Metadata = { title: "Experiments" };

export default function ExperimentsPage() {
  const { results, generated_at } = resultsIndex;
  return (
    <>
      <PageHeader
        title="Experiments"
        lede="Results rendered exclusively from the versioned result index. Each entry must reference a research run manifest with a config hash, git commit and data fingerprints."
      />
      <ResultsExplorer results={results} />
      <M5Readiness />
      {results.length === 0 ? (
        <div role="status" className="rounded-lg border border-line bg-surface-muted p-6">
          <p className="font-medium">No recorded research results yet.</p>
          <p className="mt-1 text-ink-muted">
            Results appear here once verified research runs are exported (from M3 onward).
            Smoke-test and synthetic-data runs are rejected by the result schema.
          </p>
        </div>
      ) : (
        <>
          <p className="mb-4 text-sm text-ink-muted">Index generated {generated_at}</p>
          <Section title="Macro-F1">
            <StatusBadge kind="research" />
            <ResultsChart results={results} metric="macro_f1" />
          </Section>
          <Section title="All results">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th scope="col" className="py-2 pr-4">Dataset</th>
                    <th scope="col" className="py-2 pr-4">Model</th>
                    <th scope="col" className="py-2 pr-4">Evaluation</th>
                    <th scope="col" className="py-2 pr-4">Metrics</th>
                    <th scope="col" className="py-2">Run</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.id} className="border-b border-line align-top">
                      <td className="py-2 pr-4">{r.dataset}</td>
                      <td className="py-2 pr-4">{r.model}</td>
                      <td className="py-2 pr-4">{r.evaluation}</td>
                      <td className="py-2 pr-4 font-mono text-xs">
                        {Object.entries(r.metrics)
                          .map(([k, v]) => `${k}=${v.toFixed(4)}`)
                          .join(" ")}
                      </td>
                      <td className="py-2 font-mono text-xs"><a className="underline" href={r.provenance.manifest_url}>{r.provenance.run_id}</a></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </>
      )}
    </>
  );
}
