"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

import styles from "./paper.module.css";

export type ReadingMode = "modern" | "classic";
const STORAGE_KEY = "driftguard-paper-mode";

function readStoredMode(): ReadingMode | null {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get("view");
    if (fromUrl === "modern" || fromUrl === "classic") return fromUrl;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "modern" || stored === "classic" ? stored : null;
  } catch {
    return null;
  }
}

/** Reading-mode switch, progress bar and scroll-spied contents for the manuscript page. */
export function PaperShell({
  toc,
  citation,
  children,
}: {
  toc: { id: string; title: string }[];
  citation: string;
  children: ReactNode;
}) {
  const [mode, setMode] = useState<ReadingMode>("modern");
  const [active, setActive] = useState(toc[0]?.id ?? "");
  const [progress, setProgress] = useState(0);
  const [copied, setCopied] = useState(false);
  const articleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = readStoredMode();
    // Restoring a saved preference after hydration keeps server and client markup identical.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (stored) setMode(stored);
  }, []);

  const choose = (next: ReadingMode) => {
    setMode(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* storage unavailable: the choice still applies for this visit */
    }
  };

  useEffect(() => {
    const onScroll = () => {
      const el = articleRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      setProgress(total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0);
      // The current section is the last heading that has scrolled above the sticky toolbar.
      let current = toc[0]?.id ?? "";
      for (const t of toc) {
        const h = document.getElementById(t.id);
        if (h && h.getBoundingClientRect().top < 140) current = t.id;
      }
      setActive(current);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [toc, mode]);

  const copyCitation = async () => {
    try {
      await navigator.clipboard.writeText(citation);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const contents = (
    <ol>
      {toc.map((t) => (
        <li key={t.id}>
          <a href={`#${t.id}`} aria-current={active === t.id ? "location" : undefined}>
            {t.title}
          </a>
        </li>
      ))}
    </ol>
  );

  return (
    <div className={styles.shell} data-mode={mode}>
      <div className={styles.progress} aria-hidden="true">
        <span style={{ transform: `scaleX(${progress})` }} />
      </div>

      <div className={styles.toolbar}>
        <div role="group" aria-label="Reading view" className={styles.modeSwitch}>
          <button type="button" aria-pressed={mode === "modern"} onClick={() => choose("modern")}>
            <span aria-hidden="true">◆</span> Modern
          </button>
          <button type="button" aria-pressed={mode === "classic"} onClick={() => choose("classic")}>
            <span aria-hidden="true">¶</span> Classic paper
          </button>
        </div>
        <div className={styles.toolActions}>
          <button type="button" onClick={copyCitation}>
            {copied ? "Citation copied" : "Copy citation"}
          </button>
          <button
            type="button"
            onClick={() => {
              choose("classic");
              window.setTimeout(() => window.print(), 50);
            }}
          >
            Print / PDF
          </button>
        </div>
        <span className={styles.srOnly} aria-live="polite">
          {mode === "modern" ? "Modern interactive view" : "Classic paper view"}
        </span>
      </div>

      <div className={styles.layout}>
        <nav aria-label="Paper contents" className={styles.toc}>
          <p className={styles.tocTitle}>Contents</p>
          {contents}
          <p className={styles.tocProgress}>{Math.round(progress * 100)}% read</p>
        </nav>
        <details className={styles.tocMobile}>
          <summary>Contents</summary>
          <nav aria-label="Paper contents (compact)">{contents}</nav>
        </details>
        <div ref={articleRef} className={styles.article}>
          {children}
        </div>
      </div>
    </div>
  );
}
