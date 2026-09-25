"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import recording from "@/data/stream-recording.json";
import { completionRate, snapshotSchema, type Snapshot } from "@/lib/streaming";
import { Card } from "./ui";

const recorded = snapshotSchema.parse(recording);
const number = (value: number | null | undefined, unit = "") => value == null ? "Not measured" : `${value.toFixed(2)}${unit}`;

export function StreamingDemo() {
  const [live, setLive] = useState<Snapshot | null>(null);
  const [state, setState] = useState<"loading" | "connected" | "offline">("loading");
  const [checkedAt, setCheckedAt] = useState<number>(0);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const response = await fetch("/api/stream", { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(6000)]) });
        if (!response.ok) throw new Error("unavailable");
        const snapshot = snapshotSchema.parse(await response.json());
        if (!controller.signal.aborted) { setLive(snapshot); setState("connected"); setCheckedAt(Date.now()); }
      } catch {
        if (!controller.signal.aborted) { setLive(null); setState("offline"); }
      } finally {
        if (!controller.signal.aborted) timer = setTimeout(poll, 5000);
      }
    }
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, []);
  const snapshot = live ?? recorded;
  const summary = snapshot.summary;
  const last = summary.last_prediction_utc;
  const fresh = live && last && checkedAt - Date.parse(last) < 30000 && checkedAt >= Date.parse(last);
  const duplicate = summary.counters.duplicates_suppressed ?? 0;
  const dropped = (summary.counters.dropped_queue_full ?? 0) + (summary.counters.dropped_rate_limited ?? 0);
  return <section aria-label="Streaming demonstration" className="space-y-6">
    <div className="rounded-xl border border-accent/40 bg-surface-muted p-5 sm:p-7">
      <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-accent">MQTT 5 · Read-only observatory</p>
      <p role="status" className="text-xl font-semibold">{state === "loading" ? "Connecting to streaming backend…" : state === "connected" ? "Streaming API connected" : "Backend offline · Recorded demonstration"}</p>
      <p className="mt-3 text-sm text-ink-muted">{live ? "Live API aggregates. The broker and worker have no health heartbeat; API connectivity alone does not establish that they are running." : `Recorded synthetic workstation demonstration · ${recording.recorded_at_utc}. These are measured software-demo values, not real-dataset research findings.`}</p>
      <p className="mt-2 text-sm text-simulated">Non-reportable demonstration. Replay timing is imposed, not original dataset time. No physical edge-device measurements.</p>
    </div>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card title="Model activity"><p className="text-lg text-ink">{live ? fresh ? "Recent predictions observed" : "Idle or stale — no recent predictions" : "Recorded synthetic Decision Tree"}</p><p>Models observed: {summary.model_sha256.length}. This is historical activity, not a health check.</p></Card>
      <Card title="Processing throughput"><p className="text-2xl text-accent">{number(completionRate(summary), " events/s")}</p><p>Average over retained prediction completions; not an instantaneous rate.</p></Card>
      <Card title="Replay rate"><p className="text-lg text-ink">{live ? "Not reported by live API" : `${number(recording.replay.achieved_rate_per_s)} / ${number(recording.replay.target_rate_per_s)} events/s`}</p><p>{live ? "Producer measurements must be collected separately." : "Achieved / requested producer rate, imposed schedule."}</p></Card>
      <Card title="Warm inference latency"><p className="text-2xl text-accent">{number(summary.inference_ms.p95, " ms")} <span className="text-sm">p95</span></p><p>p50 {number(summary.inference_ms.p50, " ms")} · p99 {number(summary.inference_ms.p99, " ms")}. Batch size 1, workstation.</p></Card>
      <Card title="Message-to-alert latency"><p className="text-2xl text-accent">{number(summary.end_to_end_ms.p95, " ms")} <span className="text-sm">p95</span></p><p>Send to worker completion; excludes dashboard delivery. Valid only with producer and worker on one host.</p></Card>
      <Card title="Message handling"><p>Predicted: {summary.events_by_status.predicted ?? 0}</p><p>Duplicates: {duplicate}</p><p>Rejected: {summary.events_by_status.rejected ?? 0} · Dropped: {dropped}</p><p>Unavailable model: {summary.events_by_status.model_unavailable ?? 0}</p></Card>
    </div>
    <div className="grid gap-4 md:grid-cols-2">
      <Card title="Aggregate classifications"><ul className="space-y-2">{Object.entries(summary.predictions_by_decision).map(([label, count]) => <li key={label} className="flex justify-between gap-3"><span className="break-all">{label}</span><span className="font-mono text-ink">{count}</span></li>)}</ul>{!Object.keys(summary.predictions_by_decision).length ? <p>No predictions received.</p> : null}</Card>
      <Card title="Output-shift monitor"><p className="font-semibold text-simulated">ADWIN output-mix signal · Uncalibrated</p><p>Recorded alarms: {summary.monitor_alarms}</p><p>This is not a scientifically validated concept-drift detector. An alarm does not establish a new attack or concept change.</p></Card>
    </div>
    <Card title="Recent alerts">
      {snapshot.events.length ? <ul className="space-y-3">{snapshot.events.map((event, index) => <li key={`${event.received_at_utc}-${index}`} className="flex flex-wrap justify-between gap-2 border-b border-line pb-2"><time className="break-all">{event.received_at_utc}</time><span>{event.status} · {event.decision ?? "No classification"} · {event.evidence_tier ?? "Unverified"}</span></li>)}</ul> : <p>{live ? "No recent alerts." : "The archived recording contains aggregates only; individual alerts were not retained."}</p>}
    </Card>
    <Card title="Model version and dataset provenance">
      {summary.model_sha256.map((hash) => <p key={hash} className="break-all font-mono text-xs">SHA-256: {hash}</p>)}
      <p>Evidence: {Object.keys(summary.events_by_evidence_tier).join(", ") || "Not reported"}</p>
      <p>{live ? "Dataset fingerprint is not exposed by this API version. Do not infer dataset admission from a model hash." : "Synthetic held-out fixture rows. No official Edge-IIoTset file or admitted real model was used."}</p>
      {!live ? <p className="break-all">Recording source commit: {recording.git_commit}</p> : null}
      <p>Last prediction: {last ?? "Not observed"}</p>
    </Card>
    <Card title="Verified experiment results"><p>Streaming measurements are separate from the publication gate.</p><Link className="text-accent underline" href="/experiments">View verified experiment results and admission status</Link></Card>
  </section>;
}
