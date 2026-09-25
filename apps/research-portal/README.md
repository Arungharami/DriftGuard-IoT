# DriftGuard-IoT research portal

Next.js (App Router) + TypeScript + Tailwind CSS v4 + Recharts. Deployed to Vercel (M8).

```bash
npm ci
npm run dev        # http://localhost:3000
npm run lint && npm run typecheck && npm test && npm run build
```

## Data contract

Research metrics are rendered **only** from `src/data/results/index.json`, validated at
build time by `src/lib/results.ts`. Each entry must carry research-kind provenance
(`kind: "research"`, `synthetic_data: false`, a config hash, git commit and data
fingerprints), so smoke and synthetic runs cannot be displayed as results. The index is
empty until verified research runs exist (M3+).

Simulated demonstrations (Drift Lab, M8) are labelled with a "Simulated demonstration"
badge and never read from the results index.

## Vercel

Set the project root directory to `apps/research-portal`. Server-only variables
(`INFERENCE_API_URL`, `INFERENCE_API_TOKEN`) are configured in Vercel, never with a
`NEXT_PUBLIC_` prefix. Preview deployments per PR are enabled in M8.


## Read-only MQTT observatory

`/demo` polls the server-side `/api/stream` adapter every five seconds. Configure
`DRIFTGUARD_STREAM_API_URL` (HTTPS origin, no path/query/userinfo) and
`DRIFTGUARD_DEMO_API_TOKEN` on the portal server only. The token must match the
streaming API. Never prefix either variable with `NEXT_PUBLIC_`. Local development
allows HTTP only on loopback; production requires HTTPS, even for loopback.
The adapter uses fixed read-only paths, rejects redirects, bounds decoded responses,
times out requests, strips unapproved fields and sets `private, no-store`.
The existing API token bucket also limits backend requests across portal visitors.
Keep Vercel Authentication enabled for **all** deployments before configuring live access.

Unavailable, invalid or unauthorized upstream responses show a recorded synthetic
workstation demonstration from `docs/evidence/streaming/2026-09-23-tier-a-synthetic-demo.json`.
The recording contains aggregates only; no fake individual alerts are generated.
UI tests cover desktop/mobile, accessibility, loading, connected, stale and failed states.
A connected API is not proof of worker/broker health. Verified-bundle dataset fingerprints are available from current workers. For completed
producer rates, pass `--metrics-store .local/stream/events.sqlite3` to same-host replay.
This records only measured rates, completion time, evidence tier and dataset digest;
it is the last completed replay, not current producer activity. Older API versions
without these fields show unavailable, never inferred values.
Processing rate is (retained predictions - 1)/(last completion - first completion),
not instantaneous throughput. No demo measurements enter the research result index.

Automatic Git deployments are disabled in both Vercel configs. Controlled previews
remain available through the existing manually dispatched, review-gated workflow;
production requires separate authorization. The live project is intentionally not
recreated or deployed by this integration change.
