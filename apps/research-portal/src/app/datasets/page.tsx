import type { Metadata } from "next";

import { PageHeader, Section, StatusBadge } from "@/components/ui";
import { USE_LABEL, catalog, type Dataset } from "@/lib/datasets";

export const metadata: Metadata = { title: "Datasets" };

function Terms({ d }: { d: Dataset }) {
  const rows: [string, string][] = [
    ["Academic use", USE_LABEL[d.license.academic_use] ?? d.license.academic_use],
    ["Commercial use", USE_LABEL[d.license.commercial_use] ?? d.license.commercial_use],
    ["Raw redistribution", USE_LABEL[d.license.raw_redistribution] ?? d.license.raw_redistribution],
    [
      "Model/artifact release",
      USE_LABEL[d.license.derived_artifact_redistribution] ??
        d.license.derived_artifact_redistribution,
    ],
    ["Attribution required", d.license.attribution_required ? "Yes" : "No"],
  ];
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-4 border-b border-line py-1">
          <dt className="text-ink-muted">{k}</dt>
          <dd className="font-medium">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function DatasetsPage() {
  return (
    <>
      <PageHeader
        title="Datasets"
        lede="Provenance, license terms and schema status from the project's dataset registry. This project never redistributes raw data."
      />
      {catalog.datasets.map((d) => (
        <Section key={d.id} title={d.name}>
          <article className="space-y-4 rounded-lg border border-line p-5">
            <p className="text-sm text-ink-muted">
              {d.publisher} ·{" "}
              <a className="underline" href={d.homepage}>
                publisher page
              </a>
            </p>
            <p>{d.description}</p>
            <div className="space-y-2">
              <h3 className="font-semibold">License: {d.license.name}</h3>
              <p className="text-sm text-ink-muted">
                {d.license.verified_on
                  ? `Checked against the primary source on ${d.license.verified_on}. `
                  : "Not yet verified. "}
                <a className="underline" href={d.license.source_url}>
                  Source
                </a>
              </p>
              <Terms d={d} />
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold">Tables</h3>
              <ul className="space-y-2 text-sm">
                {d.tables.map((t) => (
                  <li key={t.id} className="flex flex-wrap items-center gap-2">
                    <code className="font-mono">{t.filename}</code>
                    <StatusBadge
                      kind={t.schema_status === "confirmed" ? "research" : "planned"}
                      label={`Schema ${t.schema_status}`}
                    />
                    <span className="text-ink-muted">
                      {t.n_columns} columns · {t.n_candidate_features} candidate features ·{" "}
                      {t.n_private_columns} private columns withheld · label{" "}
                      <code>{t.label_column}</code> ·{" "}
                      {t.fingerprint_recorded ? "fingerprint recorded" : "fingerprint not yet recorded"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="text-sm text-ink-muted">
              Acquisition:{" "}
              {d.acquisition.method === "kaggle"
                ? `first-party Kaggle upload (${d.acquisition.kaggle_slug}) using your own credentials`
                : "manual download from the publisher"}
              .
            </p>
            <details className="text-sm">
              <summary className="cursor-pointer font-medium">
                Required citations ({d.citations.length})
              </summary>
              <ol className="mt-2 list-decimal space-y-1 pl-6 text-ink-muted">
                {d.citations.map((c) => (
                  <li key={c.text}>
                    {c.text}
                    {c.doi ? (
                      <>
                        {" "}
                        <a className="underline" href={`https://doi.org/${c.doi}`}>
                          doi:{c.doi}
                        </a>
                      </>
                    ) : null}
                  </li>
                ))}
              </ol>
            </details>
          </article>
        </Section>
      ))}
    </>
  );
}
