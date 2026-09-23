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
