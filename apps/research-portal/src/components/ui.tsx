import type { ReactNode } from "react";

export type StatusKind = "research" | "simulated" | "planned";

const BADGE: Record<StatusKind, { className: string; text: string }> = {
  research: { className: "border-research text-research", text: "Recorded research result" },
  simulated: { className: "border-simulated text-simulated", text: "Simulated demonstration" },
  planned: { className: "border-planned text-planned", text: "Planned" },
};

/** The text label is always shown so the distinction never relies on colour alone. */
export function StatusBadge({ kind, label }: { kind: StatusKind; label?: string }) {
  const style = BADGE[kind];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${style.className}`}
    >
      {label ?? style.text}
    </span>
  );
}

export function PageHeader({
  title,
  lede,
  milestone,
}: {
  title: string;
  lede: ReactNode;
  milestone?: string;
}) {
  return (
    <div className="mb-8 space-y-3">
      {milestone ? <StatusBadge kind="planned" label={`Content arrives in ${milestone}`} /> : null}
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
      <p className="max-w-3xl text-lg text-ink-muted">{lede}</p>
    </div>
  );
}

/** Placeholder for content scheduled in a later milestone. */
export function Planned({ milestone, children }: { milestone: string; children: ReactNode }) {
  return (
    <section
      aria-label={`Planned for ${milestone}`}
      className="rounded-lg border border-dashed border-line bg-surface-muted p-5"
    >
      <p className="mb-2 text-sm font-medium text-planned">Scheduled for {milestone}</p>
      <div className="space-y-2 text-ink-muted">{children}</div>
    </section>
  );
}

export function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-line p-5">
      <h2 className="mb-2 font-semibold">{title}</h2>
      <div className="space-y-2 text-sm text-ink-muted">{children}</div>
    </div>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-10 space-y-4">
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}
