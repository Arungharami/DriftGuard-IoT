"use client";

import { useEffect, useState } from "react";
import styles from "./WorkflowExplainer.module.css";

const STAGES = [
  { title: "IoT devices", short: "Observe traffic", icon: "01", evidence: "Proposed device input", text: "Sensors, cameras and industrial devices exchange network traffic. Our current demonstration replays synthetic flow records; it does not capture a real sensor installation.", output: "Input: synthetic network-flow records" },
  { title: "MQTT gateway", short: "Transport events", icon: "02", evidence: "Implemented with synthetic replay", text: "An authenticated MQTT broker transports replay events to a worker. Message validation, bounded queues and rate limits help keep the demonstration controlled.", output: "Output: validated flow events" },
  { title: "Edge inference", short: "Check the pattern", icon: "03", evidence: "Software foundation", text: "The worker checks for an approved model and matching feature contract before inference. If the model is unavailable, it fails closed. This animation does not run a trained intrusion detector.", output: "Output: a model decision, or an unavailable-model event" },
  { title: "Drift monitoring", short: "Notice change", icon: "04", evidence: "Research evaluation proposed", text: "The proposed research compares changing feature distributions and monitors performance when labels arrive. A drift alert alone does not prove an attack. Updates would use only labels available at that time.", output: "Proposed decision: retain the model or evaluate an update" },
  { title: "Digital dashboard", short: "Review evidence", icon: "05", evidence: "Portal and event logging", text: "Event logging and the portal make the workflow visible. Synthetic demonstrations, approved research results and planned work must remain clearly identified. No live device connection is established by pressing Play.", output: "Output: traceable events and clearly labeled evidence" },
] as const;

export function WorkflowExplainer() {
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [angled, setAngled] = useState(true);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => { setReducedMotion(media.matches); if (media.matches) setPlaying(false); };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!playing || reducedMotion) return;
    const timer = window.setInterval(() => setActive((step) => (step + 1) % STAGES.length), 5000);
    return () => window.clearInterval(timer);
  }, [playing, reducedMotion]);

  const stage = STAGES[active]!;
  function selectStage(index: number) { setActive(index); setPlaying(false); }

  return (
    <section id="how-it-works" className={styles.explainer} aria-labelledby="workflow-title">
      <div className={styles.heading}>
        <div><p className={styles.eyebrow}>Our project, explained visually</p><h2 id="workflow-title">How DriftGuard-IoT works</h2></div>
        <span className={styles.badge}>Concept animation / synthetic inputs</span>
      </div>
      <p className={styles.intro}>Follow a traffic event through our proposed device-to-cloud workflow. Select a stage or play the guided 3D sequence.</p>
      <div className={`${styles.scene} ${playing && !reducedMotion ? styles.running : ""} ${angled ? "" : styles.flat}`}>
        <div className={styles.rail} aria-hidden="true"><span /></div>
        <ol className={styles.nodes} aria-label="Workflow stages">
          {STAGES.map((item, index) => <li key={item.title}>
            <button type="button" className={`${styles.node} ${active === index ? styles.selected : ""}`} aria-pressed={active === index} aria-controls="workflow-caption" onClick={() => selectStage(index)}>
              <span className={styles.model} aria-hidden="true"><span className={styles.cube}><span className={styles.cubeFace}>{item.icon}<span className={styles.indicator} /></span></span></span>
              <span className={styles.nodeTitle}>{item.title}</span><span className={styles.nodeLabel}>{item.short}</span>
            </button>
          </li>)}
        </ol>
        <p className={styles.flowNote}>Feature drift monitoring complements inference. Adaptation requires an evaluated model and available labels.</p>
      </div>
      <div className={styles.controls} role="group" aria-label="Animation controls">
        <button type="button" className={styles.play} disabled={reducedMotion} onClick={() => setPlaying((value) => !value)}>{playing ? "Pause animation" : "Play animation"}</button>
        <button type="button" onClick={() => selectStage((active + STAGES.length - 1) % STAGES.length)}>Previous stage</button>
        <button type="button" onClick={() => selectStage((active + 1) % STAGES.length)}>Next stage</button>
        <button type="button" aria-pressed={angled} onClick={() => setAngled((value) => !value)}>{angled ? "Use flat view" : "Use 3D view"}</button>
        <span className={styles.counter}>Stage {active + 1} of {STAGES.length}</span>
      </div>
      {reducedMotion ? <p className={styles.motionNote}>Reduced motion is enabled. Use the stage buttons to explore at your own pace.</p> : null}
      <div id="workflow-caption" className={styles.caption} aria-live={playing ? "off" : "polite"} aria-atomic="true">
        <div><p className={styles.evidence}>{stage.evidence}</p><h3>{stage.title}</h3><p>{stage.text}</p></div>
        <p className={styles.output}>{stage.output}</p>
      </div>
      <p className={styles.footer}>Illustrative sequence with captions, not a recorded experiment or live telemetry feed. <a href="/architecture">Explore the architecture</a> or <a href="/demo">open the separate software demo</a>.</p>
    </section>
  );
}
