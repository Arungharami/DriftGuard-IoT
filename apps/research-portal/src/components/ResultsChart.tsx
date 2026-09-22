"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ResultEntry } from "@/lib/results";

/** Bar chart of one metric across recorded research results. Renders nothing without data. */
export function ResultsChart({ results, metric }: { results: ResultEntry[]; metric: string }) {
  const data = results
    .filter((r) => metric in r.metrics)
    .map((r) => ({ name: `${r.dataset} / ${r.model}`, value: r.metrics[metric] }));
  if (data.length === 0) return null;
  return (
    <figure aria-label={`${metric} by dataset and model`} className="h-80 w-full">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" />
          <XAxis dataKey="name" tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }} />
          <YAxis domain={[0, 1]} tick={{ fill: "var(--color-ink-muted)", fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="value" name={metric} fill="var(--color-research)" />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}
