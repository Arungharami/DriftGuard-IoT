import Link from "next/link";

import { NavLinks } from "./NavLinks";

export function SiteHeader() {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="font-semibold tracking-tight">
          DriftGuard<span className="text-accent">-IoT</span>
        </Link>
        {/* Native disclosure keeps the mobile menu usable without JavaScript. */}
        <details className="relative lg:hidden">
          <summary className="cursor-pointer list-none rounded border border-line px-3 py-1.5 text-sm">
            Menu
          </summary>
          <nav
            aria-label="Primary"
            className="absolute right-0 z-40 mt-2 w-56 rounded border border-line bg-surface p-2 shadow-lg"
          >
            <NavLinks orientation="vertical" />
          </nav>
        </details>
      </div>
      <nav aria-label="Primary" className="mx-auto hidden max-w-5xl px-6 pb-2 lg:block">
        <NavLinks orientation="horizontal" />
      </nav>
    </header>
  );
}
