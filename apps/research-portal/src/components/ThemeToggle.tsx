"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");
  useEffect(() => {
    const saved = window.localStorage.getItem("driftguard-theme");
    const next: Theme = saved === "light" || saved === "dark" ? saved : (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    document.documentElement.dataset.theme = next;
    setTheme(next);
  }, []);
  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    window.localStorage.setItem("driftguard-theme", next);
    setTheme(next);
  };
  return <button type="button" onClick={toggle} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`} title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`} className="inline-flex h-10 items-center gap-2 rounded-full border border-line bg-surface-muted px-3 text-xs font-semibold text-ink shadow-sm transition hover:border-accent focus-visible:outline">
    <span aria-hidden="true" className="text-base">{theme === "dark" ? "☀" : "☾"}</span>
    <span className="hidden sm:inline">{theme === "dark" ? "Day" : "Night"}</span>
  </button>;
}
