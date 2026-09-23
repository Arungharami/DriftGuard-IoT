"use client";

import { useState } from "react";
import { m5Audit } from "@/lib/m5";

const repository = "https://github.com/Arungharami/DriftGuard-IoT";

export function M5Readiness() {
  const [selected, setSelected] = useState("all");
  const experiments = m5Audit.experiments.filter((item) => selected === "all" || item.id === selected);
  return (
    <section aria-labelledby="m5-heading" className="my-8 rounded-lg border border-line p-6">
      <h2 id="m5-heading" className="text-2xl font-semibold">M5 evidence and readiness</h2>
      <p role="status" className="my-3 font-medium">Research campaign blocked — no M5 research results.</p>
      <p className="text-ink-muted">Repository audit: {m5Audit.audited_on}. Evaluation utilities and synthetic checks do not establish IoT/IIoT generalization.</p>
      <details className="my-4">
        <summary className="cursor-pointer font-medium">Inspect M0–M4 evidence</summary>
        <ul className="mt-3 space-y-3">
          {m5Audit.milestones.map((milestone) => (
            <li key={milestone.id}>
              <a className="underline" href={milestone.evidence}>{milestone.id}: {milestone.status}</a>
              <p>{milestone.detail}</p>
            </li>
          ))}
        </ul>
        <p className="mt-3 break-all text-sm">Verified branch base: <a className="underline" href={`${repository}/commit/${m5Audit.base_commit}`}>{m5Audit.base_commit}</a></p>
      </details>
      <label className="block font-medium" htmlFor="m5-area">Experiment area</label>
      <select id="m5-area" value={selected} onChange={(event) => setSelected(event.target.value)} className="my-2 w-full rounded border border-line bg-surface p-2 text-ink">
        <option value="all">All areas</option>
        {m5Audit.experiments.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
      </select>
      <div aria-live="polite" className="space-y-4">
        {experiments.map((item) => (
          <article key={item.id} className="rounded border border-line p-4">
            <h3 className="font-semibold">{item.title} · Blocked</h3>
            <p className="my-2">{item.implementation}</p>
            <ul className="list-disc space-y-1 pl-5">{item.blockers.map((reason) => <li key={reason}>{reason}</li>)}</ul>
            <a className="mt-3 inline-block underline" href={`${repository}/blob/m5/generalization-audit/${item.evidence}`}>Evidence and protocol</a>
          </article>
        ))}
      </div>
    </section>
  );
}
