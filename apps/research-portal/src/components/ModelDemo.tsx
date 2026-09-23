"use client";
import { useState } from "react";

export function ModelDemo() {
  const [input, setInput] = useState('{"rows": [{}]}');
  const [message, setMessage] = useState("No approved model is connected. Predictions will appear only after model and license review.");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true);
    try {
      const body = JSON.parse(input);
      const response = await fetch("/api/inference", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const result = await response.json();
      setMessage(response.ok ? `Model ${result.model_version}: ${result.predictions.join(", ")}` : result.error);
    } catch { setMessage("Could not process the request. Check JSON formatting and connection."); }
    finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="space-y-4 rounded-xl border border-line bg-surface-muted p-6">
    <p>Use only the approved feature schema. Do not submit IP addresses, identifiers, or captured payloads.</p>
    <label htmlFor="inference-input" className="block font-medium">Feature rows (JSON)</label>
    <textarea id="inference-input" value={input} onChange={(event) => setInput(event.target.value)} rows={7} maxLength={32768} className="w-full rounded border border-line bg-surface p-3 font-mono text-sm" />
    <button disabled={busy} className="rounded bg-accent px-4 py-2 font-semibold text-accent-ink disabled:opacity-50">{busy ? "Checking…" : "Check model service"}</button>
    <p role="status" aria-live="polite">{message}</p>
  </form>;
}
