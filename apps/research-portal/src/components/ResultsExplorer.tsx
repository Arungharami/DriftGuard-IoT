"use client";
import { useState } from "react";
import type { ResultEntry } from "@/lib/results";
import { ResultsChart } from "./ResultsChart";

export function ResultsExplorer({ results }: { results: ResultEntry[] }) {
  const [dataset, setDataset] = useState("all");
  const visible = results.filter((result) => dataset === "all" || result.dataset === dataset);
  return <section className="space-y-4">
    <label htmlFor="dataset-filter" className="block font-medium">Filter verified results by dataset</label>
    <select id="dataset-filter" value={dataset} onChange={(event) => setDataset(event.target.value)} className="rounded border border-line bg-surface p-2">
      <option value="all">All datasets</option>
      {[...new Set(results.map((result) => result.dataset))].map((name) => <option key={name}>{name}</option>)}
    </select>
    {visible.length ? <><ResultsChart results={visible} metric="macro_f1" /><ul>{visible.map((result) => <li key={result.id}>{result.model} · {result.dataset} · <a className="underline" href={result.provenance.manifest_url}>Verified manifest</a></li>)}</ul></> : <p role="status">No verified results match this selection. No values have been simulated for this chart.</p>}
  </section>;
}
