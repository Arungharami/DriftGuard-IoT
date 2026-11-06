import { readFileSync } from "node:fs";
import { join } from "node:path";

import katex from "katex";
import "katex/dist/katex.min.css";
import type { Metadata } from "next";
import Image from "next/image";
import type { ReactNode } from "react";

import { BatteryCalculator, CostChart, F1Chart, TracesChart } from "@/components/paper/PaperCharts";
import { PaperShell } from "@/components/paper/PaperShell";
import styles from "@/components/paper/paper.module.css";
import { StatusBadge } from "@/components/ui";
import { REPO_URL } from "@/content/site";
import { parsePaper, tokenizeInline, type PaperBlock } from "@/lib/paper";

export const metadata: Metadata = {
  title: "Paper",
  description:
    "DriftGuard-IoT: drift-aware, delayed-label intrusion detection for resource-constrained IoT edge gateways. CNT 6167 group research paper with interactive figures.",
};

const NOTEBOOK_PATH = "notebooks/10_cnt6167_paper_calculations.ipynb";
const COLAB_URL = `https://colab.research.google.com/github/Arungharami/DriftGuard-IoT/blob/main/${NOTEBOOK_PATH}`;

const FIGURES: Record<string, { w: number; h: number; alt: string }> = {
  fig_architecture: { w: 2400, h: 1040, alt: "Three-tier architecture: ESP32 nodes, MQTT broker, and the DriftGuard gateway with its ADWIN-triggered windowed refit loop." },
  fig_circuit: { w: 2659, h: 990, alt: "Schematic of the ESP32 sensor node with Li-ion cell, MCP1700 regulator, battery-sense divider, DHT22 sensor and status LED." },
  fig_map: { w: 2200, h: 1120, alt: "World map marking the TON_IoT, WUSTL-IIoT-2021 and Edge-IIoTset origins and the study site in Boca Raton." },
  fig_f1_post: { w: 2200, h: 840, alt: "Grouped bar chart of post-drift macro-F1 for five policies and three models under covariate and concept drift." },
  fig_traces: { w: 2200, h: 760, alt: "Rolling accuracy curves for five policies before and after the drift onset at flow 3,000." },
  fig_cost_benefit: { w: 1720, h: 840, alt: "Scatter plot of retraining time against macro-F1 gain for each policy and model." },
};

const INTERACTIVE: Record<string, (caption: string) => ReactNode> = {
  fig_f1_post: (c) => <F1Chart caption={c} />,
  fig_traces: (c) => <TracesChart caption={c} />,
  fig_cost_benefit: (c) => <CostChart caption={c} />,
};

const KEY_FINDINGS = [
  { value: "0.92 → 0.25", label: "macro-F1 of a frozen model after concept drift" },
  { value: "15 / 15", label: "concept drifts caught by ADWIN, median 140 flows" },
  { value: "86–92 %", label: "of periodic retraining's gain recovered by ADWIN-window" },
  { value: "3–11 %", label: "of periodic retraining's compute needed to do it" },
];

function Inline({ text }: { text: string }) {
  return (
    <>
      {tokenizeInline(text).map((t, i) => {
        switch (t.kind) {
          case "bold":
            return <strong key={i}>{t.value}</strong>;
          case "italic":
            return <em key={i}>{t.value}</em>;
          case "cite":
            return (
              <a key={i} href={`#ref-${t.n}`} className={styles.cite} aria-label={`Reference ${t.n}`}>
                [{t.n}]
              </a>
            );
          case "link":
            return (
              <a key={i} href={t.href} className={styles.link} rel="noreferrer">
                {t.value}
              </a>
            );
          default:
            return <span key={i}>{t.value}</span>;
        }
      })}
    </>
  );
}

function splitNumeral(text: string): { numeral: string; rest: string } {
  const m = text.match(/^([IVX]+|[A-H])\.\s+(.*)$/);
  return m ? { numeral: m[1] ?? "", rest: m[2] ?? text } : { numeral: "", rest: text };
}

function Block({ block }: { block: PaperBlock }) {
  switch (block.type) {
    case "h2": {
      const { numeral, rest } = splitNumeral(block.text);
      return (
        <h2 id={block.id} className={styles.h2}>
          {numeral ? <span className={styles.numeral}>{numeral}.</span> : null}
          <span>{rest}</span>
        </h2>
      );
    }
    case "h3": {
      const { numeral, rest } = splitNumeral(block.text);
      return (
        <h3 id={block.id} className={styles.h3}>
          {numeral ? <span className={styles.numeral}>{numeral}.</span> : null}
          <span>{rest}</span>
        </h3>
      );
    }
    case "p":
      return (
        <p className={styles.p}>
          <Inline text={block.text} />
        </p>
      );
    case "caption":
      return (
        <p className={styles.tableCaption}>
          <Inline text={block.text} />
        </p>
      );
    case "list": {
      const Tag = block.ordered ? "ol" : "ul";
      return (
        <Tag className={block.ordered ? styles.ol : styles.ul}>
          {block.items.map((item, i) => (
            <li key={i}>
              <Inline text={item} />
            </li>
          ))}
        </Tag>
      );
    }
    case "table":
      return (
        <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Scrollable table">
          <table className={styles.table}>
            <thead>
              <tr>
                {block.head.map((h, i) => (
                  <th key={i} scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) =>
                    c === 0 ? (
                      <th key={c} scope="row">
                        <Inline text={cell} />
                      </th>
                    ) : (
                      <td key={c}>
                        <Inline text={cell} />
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case "math":
      return (
        <div className={styles.equation}>
          <div
            className={styles.mathBody}
            tabIndex={0}
            role="region"
            aria-label={`Equation ${block.n}`}
            // KaTeX output is generated at build time from the repository's own manuscript source.
            dangerouslySetInnerHTML={{
              __html: katex.renderToString(block.tex, { displayMode: true, throwOnError: false, output: "htmlAndMathml" }),
            }}
          />
          <span className={styles.eqNo}>({block.n})</span>
        </div>
      );
    case "figure": {
      const meta = FIGURES[block.key];
      const staticFigure = (
        <figure className={styles.figure}>
          {meta ? <Image src={`/paper/${block.key}.png`} width={meta.w} height={meta.h} alt={meta.alt} sizes="(min-width: 1024px) 760px, 100vw" /> : null}
          <figcaption className={styles.figcaption}>
            <Inline text={block.caption} />
          </figcaption>
        </figure>
      );
      const interactive = INTERACTIVE[block.key];
      if (!interactive) return staticFigure;
      return (
        <>
          <div className={styles.classicOnly}>{staticFigure}</div>
          <div className={styles.modernOnly}>{interactive(block.caption)}</div>
        </>
      );
    }
    case "widget":
      return block.key === "battery" ? (
        <div className={styles.modernOnly}>
          <BatteryCalculator />
        </div>
      ) : null;
    case "reference":
      return (
        <li id={`ref-${block.n}`} value={block.n} className={styles.reference}>
          <Inline text={block.text} />
        </li>
      );
  }
}

export default function PaperPage() {
  const paper = parsePaper(readFileSync(join(process.cwd(), "src/content/paper.md"), "utf8"));
  const readMinutes = Math.round(paper.wordCount / 230);
  const toc = paper.sections.map((s) => ({ id: s.id, title: s.title }));
  const citation = `A. K. Gharami, S. Rabbany, and A. Gajam, "${paper.title}," CNT 6167 Internet of Things, Florida Atlantic University, 2026. [Online]. Available: ${REPO_URL}`;
  const [names, course] = paper.authors.split(" — ");

  return (
    <PaperShell toc={toc} citation={citation}>
      <header className={styles.hero}>
        <div className={styles.heroMeta}>
          <StatusBadge kind="simulated" label="Controlled simulation · synthetic flows" />
          <span>CNT 6167 Internet of Things · Fall 2026</span>
          <span>
            {paper.wordCount.toLocaleString("en-US")} words · {readMinutes} min read
          </span>
        </div>
        <h1 className={styles.title}>{paper.title}</h1>
        <p className={styles.authors}>{names}</p>
        <p className={styles.affil}>{course}</p>
        <div className={`${styles.findings} ${styles.modernOnly}`}>
          {KEY_FINDINGS.map((f) => (
            <div key={f.label}>
              <span>{f.value}</span>
              <p>{f.label}</p>
            </div>
          ))}
        </div>
        <div className={`${styles.actions} ${styles.modernOnly}`}>
          <a href={COLAB_URL} className={styles.primary} rel="noreferrer">
            Open the calculations in Colab
          </a>
          <a href={`${REPO_URL}/blob/main/${NOTEBOOK_PATH}`} rel="noreferrer">
            Notebook on GitHub
          </a>
          <a href={`${REPO_URL}/tree/main/paper_calculations`} rel="noreferrer">
            Scripts and result CSVs
          </a>
        </div>
      </header>

      {paper.sections.map((section) => {
        const isRefs = section.id === "references";
        const body = section.blocks.map((b, i) => <Block key={i} block={b} />);
        if (isRefs) {
          const [heading, ...refs] = body;
          return (
            <section key={section.id} className={styles.section} aria-labelledby={section.id}>
              {heading}
              <ol className={styles.references}>{refs}</ol>
            </section>
          );
        }
        return (
          <section
            key={section.id}
            className={section.id === "abstract" ? `${styles.section} ${styles.abstract}` : styles.section}
            aria-labelledby={section.id}
          >
            {body}
          </section>
        );
      })}
    </PaperShell>
  );
}
