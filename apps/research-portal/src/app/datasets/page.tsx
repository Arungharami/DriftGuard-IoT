import type { Metadata } from "next";

import { PageHeader, Planned } from "@/components/ui";

export const metadata: Metadata = { title: "Datasets" };

const DATASETS = [
  { name: "TON_IoT", domain: "IoT / IIoT telemetry and network traffic" },
  { name: "WUSTL-IIOT-2021", domain: "Industrial IoT network traffic" },
  { name: "Edge-IIoTset", domain: "Edge IoT / IIoT traffic" },
];

export default function DatasetsPage() {
  return (
    <>
      <PageHeader
        title="Datasets"
        lede="The three public datasets used by the reference study. Raw data is never redistributed by this project."
        milestone="M1"
      />
      <div className="mb-8 overflow-x-auto">
        <table className="w-full min-w-[32rem] border-collapse text-left text-sm">
          <caption className="sr-only">Datasets and verification status</caption>
          <thead>
            <tr className="border-b border-line">
              <th scope="col" className="py-2 pr-4">Dataset</th>
              <th scope="col" className="py-2 pr-4">Domain</th>
              <th scope="col" className="py-2">License and provenance</th>
            </tr>
          </thead>
          <tbody>
            {DATASETS.map((d) => (
              <tr key={d.name} className="border-b border-line">
                <th scope="row" className="py-2 pr-4 font-medium">{d.name}</th>
                <td className="py-2 pr-4 text-ink-muted">{d.domain}</td>
                <td className="py-2 text-ink-muted">Not yet verified (M1)</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Planned milestone="M1">
        <p>
          Registry entries with source URLs, license terms, citation requirements, SHA-256
          fingerprints, class distributions and schema summaries.
        </p>
      </Planned>
    </>
  );
}
