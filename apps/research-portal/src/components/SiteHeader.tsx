import Link from "next/link";
import { NavLinks } from "./NavLinks";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-surface/90 shadow-[0_2px_20px_rgba(0,0,0,.09)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex shrink-0 items-center gap-2.5" aria-label="DriftGuard-IoT home">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#3679db] via-[#12456c] to-[#081e3d] text-[11px] font-extrabold text-white shadow-lg shadow-[#102c4e]/25">DG</span>
          <span className="leading-tight"><span className="block text-sm font-bold tracking-tight">DriftGuard-IoT</span><span className="block text-[10px] font-semibold uppercase tracking-[.16em] text-ink-muted">FAU · CNT 6167</span></span>
        </Link>
        <nav aria-label="Primary navigation" className="hidden lg:block"><NavLinks orientation="horizontal" /></nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <a href="https://github.com/Arungharami/DriftGuard-IoT" target="_blank" rel="noopener noreferrer" className="hidden rounded-full border border-line px-3 py-2 text-xs font-semibold transition hover:border-accent hover:text-accent sm:inline-flex">GitHub ↗</a>
          <details className="relative lg:hidden">
            <summary className="cursor-pointer list-none rounded-xl border border-line px-3 py-2 text-sm font-semibold marker:hidden focus-visible:outline">Menu ☰</summary>
            <nav aria-label="Mobile navigation" className="absolute right-0 top-full mt-3 max-h-[75vh] w-[min(90vw,340px)] overflow-y-auto rounded-2xl border border-line bg-surface p-3 shadow-2xl"><NavLinks orientation="vertical" /></nav>
          </details>
        </div>
      </div>
    </header>
  );
}
