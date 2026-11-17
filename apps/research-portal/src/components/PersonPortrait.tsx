"use client";

import { useEffect, useState } from "react";

type Props = { name: string; src?: string };

export function PersonPortrait({ name, src }: Props) {
  const [broken, setBroken] = useState(false);
  useEffect(() => setBroken(false), [src]);

  const initials = name.replace(/^Professor\s+/, "").split(" ").map((part) => part[0]).join("");
  const showImage = Boolean(src && !broken);
  const isLandscape = Boolean(src?.includes("beach"));

  return (
    <div className="relative mb-3 aspect-square w-full overflow-hidden rounded-xl border border-line bg-surface-muted shadow-sm">
      {showImage ? (
        // A native image avoids Next.js remote-image pipeline failures and preserves original photographs.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={src}
          src={src}
          alt={isLandscape ? `Original nighttime beach photograph supplied for ${name}` : `Portrait of ${name}`}
          loading="lazy"
          decoding="async"
          className={`absolute inset-0 h-full w-full ${isLandscape ? "object-cover object-center" : "object-cover object-top"}`}
          onError={() => setBroken(true)}
        />
      ) : (
        <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-[#1e4d76] via-[#152e4f] to-[#0d1e34] text-center text-white">
          <span aria-hidden="true" className="text-xl font-bold tracking-wide sm:text-2xl">{initials}</span>
          <span className="sr-only">{src ? "Photograph could not load" : "Photograph not supplied"}</span>
        </div>
      )}
    </div>
  );
}
