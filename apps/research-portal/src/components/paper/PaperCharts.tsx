"use client";

import { useId, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ErrorBar,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import results from "@/data/paper/results.json";
import { batteryLife } from "@/lib/paper";

import styles from "./paper.module.css";

type Scenario = "concept" | "covariate";
type Policy = "frozen" | "periodic" | "error_triggered" | "adwin" | "adwin_window";
type Cell = {
  scenario: Scenario;
  model: string;
  policy: Policy;
  f1_post: number;
  f1_post_sd: number;
  delta: number | null;
  refit_s: number;
  refits: number;
};

const CELLS = results.cells as Cell[];
const TRACES = results.traces as Record<Scenario, Array<Record<string, number>>>;

export const POLICIES: { key: Policy; label: string; color: string }[] = [
  { key: "frozen", label: "Frozen", color: "#9aa7b4" },
  { key: "periodic", label: "Periodic", color: "#8ab4ff" },
  { key: "error_triggered", label: "Error-threshold", color: "#fdba74" },
  { key: "adwin", label: "ADWIN", color: "#c9a7ff" },
  { key: "adwin_window", label: "ADWIN-window", color: "#5ee0ca" },
];
const MODELS: { key: string; label: string }[] = [
  { key: "decision_tree", label: "Decision Tree" },
  { key: "random_forest", label: "Random Forest" },
  { key: "lightgbm", label: "LightGBM" },
];
const TICK = { fill: "var(--color-ink-muted)", fontSize: 12 };
const TOOLTIP = {
  contentStyle: {
    background: "#142033",
    border: "1px solid #304157",
    borderRadius: 10,
    color: "#edf3f8",
    fontSize: 12,
  },
  itemStyle: { color: "#edf3f8" },
  labelStyle: { color: "#b1bfd0", marginBottom: 4 },
};

function ScenarioToggle({ value, onChange }: { value: Scenario; onChange: (s: Scenario) => void }) {
  return (
    <div role="group" aria-label="Drift type" className={styles.segmented}>
      {(["concept", "covariate"] as Scenario[]).map((s) => (
        <button key={s} type="button" aria-pressed={value === s} onClick={() => onChange(s)}>
          {s === "concept" ? "Concept drift" : "Covariate drift"}
        </button>
      ))}
    </div>
  );
}

function ChartFrame({
  caption,
  label,
  controls,
  children,
  note,
}: {
  caption: string;
  label: string;
  controls?: React.ReactNode;
  children: React.ReactNode;
  note?: string;
}) {
  return (
    <figure className={styles.chartCard} aria-label={label}>
      <div className={styles.chartTop}>
        <span className={styles.liveTag}>Interactive</span>
        {controls}
      </div>
      <div className={styles.chartBody}>{children}</div>
      {note ? <p className={styles.chartNote}>{note}</p> : null}
      <figcaption className={styles.figcaption}>{caption}</figcaption>
    </figure>
  );
}

export function F1Chart({ caption }: { caption: string }) {
  const [scenario, setScenario] = useState<Scenario>("concept");
  const data = useMemo(
    () =>
      MODELS.map((m) => {
        const row: Record<string, string | number> = { model: m.label };
        for (const p of POLICIES) {
          const c = CELLS.find((x) => x.scenario === scenario && x.model === m.key && x.policy === p.key);
          row[p.key] = c?.f1_post ?? 0;
          row[`${p.key}_sd`] = c?.f1_post_sd ?? 0;
        }
        return row;
      }),
    [scenario],
  );
  return (
    <ChartFrame
      caption={caption}
      label="Post-drift macro-F1 by policy and model"
      controls={<ScenarioToggle value={scenario} onChange={setScenario} />}
      note="Bars show the mean over five seeds; whiskers show ± one standard deviation."
    >
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -8 }} barCategoryGap="18%">
          <CartesianGrid vertical={false} stroke="#304157" strokeDasharray="3 3" />
          <XAxis dataKey="model" tick={TICK} tickLine={false} axisLine={{ stroke: "#304157" }} />
          <YAxis domain={[0, 1]} tick={TICK} tickLine={false} axisLine={false} />
          <Tooltip
            {...TOOLTIP}
            cursor={{ fill: "#ffffff0a" }}
            formatter={(v, name) => [Number(v).toFixed(3), String(name)]}
          />
          <Legend itemSorter={null} wrapperStyle={{ fontSize: 12, color: "#b1bfd0" }} />
          {POLICIES.map((p) => (
            <Bar key={p.key} dataKey={p.key} name={p.label} fill={p.color} radius={[3, 3, 0, 0]} isAnimationActive={false}>
              <ErrorBar dataKey={`${p.key}_sd`} width={3} stroke="#edf3f8" strokeOpacity={0.55} />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function TracesChart({ caption }: { caption: string }) {
  const [scenario, setScenario] = useState<Scenario>("concept");
  const [hidden, setHidden] = useState<Set<Policy>>(new Set());
  const toggle = (p: Policy) =>
    setHidden((h) => {
      const n = new Set(h);
      if (n.has(p)) n.delete(p);
      else n.add(p);
      return n;
    });
  return (
    <ChartFrame
      caption={caption}
      label="Rolling accuracy before and after drift"
      controls={
        <>
          <ScenarioToggle value={scenario} onChange={setScenario} />
          <div role="group" aria-label="Show or hide policies" className={styles.chips}>
            {POLICIES.map((p) => (
              <button
                key={p.key}
                type="button"
                aria-pressed={!hidden.has(p.key)}
                onClick={() => toggle(p.key)}
                style={{ ["--chip" as string]: p.color }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </>
      }
    >
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={TRACES[scenario]} margin={{ top: 12, right: 12, bottom: 4, left: -8 }}>
          <CartesianGrid stroke="#304157" strokeDasharray="3 3" />
          <XAxis
            dataKey="i"
            type="number"
            domain={[300, 6000]}
            ticks={[1000, 2000, 3000, 4000, 5000, 6000]}
            tick={TICK}
            tickLine={false}
            axisLine={{ stroke: "#304157" }}
          />
          <YAxis domain={[0.4, 1]} tick={TICK} tickLine={false} axisLine={false} />
          <Tooltip
            {...TOOLTIP}
            labelFormatter={(v) => `Flow ${v}`}
            formatter={(v, name) => [Number(v).toFixed(3), String(name)]}
          />
          <ReferenceLine
            x={3000}
            stroke="#edf3f8"
            strokeDasharray="4 4"
            label={{ value: "drift onset", fill: "#b1bfd0", fontSize: 11, position: "insideTopRight" }}
          />
          {POLICIES.map((p) => (
            <Line
              key={p.key}
              dataKey={p.key}
              name={p.label}
              stroke={p.color}
              strokeWidth={p.key === "adwin_window" ? 2.6 : 1.6}
              dot={false}
              hide={hidden.has(p.key)}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

export function CostChart({ caption }: { caption: string }) {
  const [scenario, setScenario] = useState<Scenario>("concept");
  const series = POLICIES.filter((p) => p.key !== "frozen").map((p) => ({
    ...p,
    points: CELLS.filter((c) => c.scenario === scenario && c.policy === p.key).map((c) => ({
      x: Math.max(c.refit_s, 0.001),
      y: c.delta ?? 0,
      model: MODELS.find((m) => m.key === c.model)?.label ?? c.model,
      refits: c.refits,
    })),
  }));
  return (
    <ChartFrame
      caption={caption}
      label="Retraining cost against macro-F1 gain"
      controls={<ScenarioToggle value={scenario} onChange={setScenario} />}
      note="Up and to the left is better: more recovered accuracy for less retraining. Hover a point for its model."
    >
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 18, left: -8 }}>
          <CartesianGrid stroke="#304157" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="x"
            scale="log"
            domain={[0.001, 10]}
            ticks={[0.001, 0.01, 0.1, 1, 10]}
            tickFormatter={(v) => `${v} s`}
            tick={TICK}
            tickLine={false}
            axisLine={{ stroke: "#304157" }}
            label={{ value: "Retraining time per stream (log scale)", fill: "#b1bfd0", fontSize: 11, position: "insideBottom", offset: -12 }}
          />
          <YAxis type="number" dataKey="y" tick={TICK} tickLine={false} axisLine={false} />
          <ZAxis range={[90, 90]} />
          <ReferenceLine y={0} stroke="#b1bfd0" />
          <Tooltip
            {...TOOLTIP}
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              const d = active && payload?.[0]?.payload;
              if (!d) return null;
              const s = series.find((x) => x.points.includes(d));
              return (
                <div style={TOOLTIP.contentStyle as React.CSSProperties} className={styles.tip}>
                  <strong>{s?.label}</strong> · {d.model}
                  <br />
                  Gain {d.y >= 0 ? "+" : ""}
                  {d.y.toFixed(3)} macro-F1
                  <br />
                  {d.x.toFixed(3)} s retraining, {d.refits.toFixed(1)} refits
                </div>
              );
            }}
          />
          <Legend itemSorter={null} verticalAlign="top" wrapperStyle={{ fontSize: 12, color: "#b1bfd0", paddingBottom: 6 }} />
          {series.map((s) => (
            <Scatter key={s.key} name={s.label} data={s.points} fill={s.color} isAnimationActive={false} />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

const fmt = (n: number, d = 1) => n.toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });

export function BatteryCalculator() {
  const id = useId();
  const [period, setPeriod] = useState(60);
  const [active, setActive] = useState(2);
  const [capacity, setCapacity] = useState(2600);
  const r = batteryLife({ periodS: period, activeS: active, capacityMah: capacity });
  const periodLabel = period >= 60 ? `${fmt(period / 60, period % 60 ? 1 : 0)} min` : `${period} s`;
  const max = 400;
  return (
    <section className={styles.calc} aria-labelledby={`${id}-t`}>
      <div className={styles.calcHead}>
        <span className={styles.liveTag}>Try it</span>
        <h4 id={`${id}-t`}>Sensor-node battery-life calculator</h4>
        <p>Same model as Eq. (3): 121.5 mA while sampling and publishing, 32.6 µA asleep, 80 % usable capacity.</p>
      </div>
      <div className={styles.calcGrid}>
        <div className={styles.sliders}>
          <label htmlFor={`${id}-p`}>
            Reporting interval <output>{periodLabel}</output>
          </label>
          <input id={`${id}-p`} type="range" min={10} max={1800} step={10} value={period} onChange={(e) => setPeriod(Number(e.target.value))} />
          <label htmlFor={`${id}-a`}>
            Awake time per report <output>{fmt(active)} s</output>
          </label>
          <input id={`${id}-a`} type="range" min={0.5} max={10} step={0.5} value={active} onChange={(e) => setActive(Number(e.target.value))} />
          <label htmlFor={`${id}-c`}>
            Battery capacity <output>{capacity.toLocaleString("en-US")} mAh</output>
          </label>
          <input id={`${id}-c`} type="range" min={500} max={5000} step={100} value={capacity} onChange={(e) => setCapacity(Number(e.target.value))} />
        </div>
        <div className={styles.readout} aria-live="polite">
          <div>
            <span className={styles.big}>{fmt(r.days, r.days < 10 ? 1 : 0)}</span>
            <span className={styles.unit}>days</span>
          </div>
          <div className={styles.meter} aria-hidden="true">
            <span style={{ width: `${Math.min(100, (r.days / max) * 100)}%` }} />
          </div>
          <dl>
            <div>
              <dt>Average current</dt>
              <dd>{fmt(r.avgMa, 2)} mA</dd>
            </div>
            <div>
              <dt>Reports per day</dt>
              <dd>{Math.round(86400 / period).toLocaleString("en-US")}</dd>
            </div>
            <div>
              <dt>Energy per report</dt>
              <dd>{fmt((3.7 * 121.5 * active) / 1000, 2)} J</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  );
}
