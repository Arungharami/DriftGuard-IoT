"use client";

import Image from "next/image";
import { useState } from "react";

export function PersonPortrait({ name, src }: { name: string; src?: string }) {
  const [failed, setFailed] = useState(false);
  return <div className="relative mb-4 aspect-[4/5] w-full overflow-hidden rounded-xl border border-line bg-surface-muted">
    {src && !failed ? <Image src={src} alt={`Portrait of ${name}`} fill unoptimized sizes="(max-width: 640px) 45vw, 240px" className="object-cover object-top" onError={() => setFailed(true)} /> : <div className="flex h-full flex-col items-center justify-center gap-3 p-4 text-center"><span aria-hidden="true" className="text-4xl font-semibold text-accent">{name.replace("Professor ", "").split(" ").map((part) => part[0]).join("")}</span><span className="text-xs text-ink-muted">{src ? "Portrait unavailable" : "Photo pending"}</span></div>}
  </div>;
}
