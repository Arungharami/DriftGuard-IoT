"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV } from "@/content/site";

export function NavLinks({ orientation }: { orientation: "horizontal" | "vertical" }) {
  const pathname = usePathname();
  const list =
    orientation === "horizontal" ? "flex flex-wrap gap-x-1 gap-y-1" : "flex flex-col gap-0.5";
  return (
    <ul className={list}>
      {NAV.map(({ href, label }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <li key={href}>
            <Link
              href={href}
              aria-current={active ? "page" : undefined}
              className={`block rounded px-2.5 py-1.5 text-sm ${
                active
                  ? "bg-surface-muted font-medium text-ink"
                  : "text-ink-muted hover:bg-surface-muted hover:text-ink"
              }`}
            >
              {label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
