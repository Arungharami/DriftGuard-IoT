# ADR 0001 — Project architecture

- **Status:** Accepted (M0)
- **Date:** 2026-09-22

## Context

DriftGuard-IoT must (a) reproduce five lightweight intrusion-detection baselines from
Ismail, Dandan and Qushou (2025, doi:10.1109/ACCESS.2025.3554083) on three public
datasets under a leakage-safe protocol, and (b) evaluate an independent drift-monitoring
and adaptation strategy. Results must be traceable to code, configuration, data and
environment, and must be consumable by notebooks (Colab), an inference Space (Hugging
Face) and a public portal (Vercel). No real data may enter CI or Git.

## Decision

### 1. One Python research package, `src/` layout

`src/driftguard/` is an installable package (`driftguard-iot`, built with Hatchling).
The `src/` layout ensures tests import the *installed* package, not the working tree.

| Subpackage | Responsibility | First milestone |
| --- | --- | --- |
| `data` | Dataset registry, schemas, provenance, synthetic fixtures | M0 (synthetic), M1 |
| `preprocessing` | Split-before-fit partitioning, train-only transformers | M0 (split, pipeline), M2 |
| `models` | Estimator factory for DT, RF, Bagging, Stacking, LightGBM | M0 (DT only), M2 |
| `evaluation` | Metrics, bootstrap CIs, evaluation protocols | M0 (point metrics), M3 |
| `drift` | Feature-drift statistics and detectors | M5 |
| `adaptation` | Retain / recalibrate / retrain policies | M5 |
| `explainability` | Feature importance, SHAP, selection stability | M6 |
| `benchmark` | Latency, memory, throughput, model size | M6 |
| `inference` | Validated request schema, serving adapters | M7 |
| `reporting` | Run manifests, provenance, result export | M0 (manifest), M3 |

Notebooks, the CLI and the inference Space call package functions; they do not
reimplement algorithms.

### 2. Typed, composable configuration

Experiments are YAML files under `configs/experiments/` that reference a dataset config
(`configs/datasets/`) and model configs (`configs/models/`) by relative path. Pydantic v2
models (`driftguard.config`) validate the resolved result with `extra="forbid"` so typos
fail loudly. Each `ExperimentConfig` has a canonical SHA-256 hash recorded in the run
manifest. Random seeds live only in the experiment config: model configs may not set
`random_state`.

### 3. Leakage safety is structural

Partitioning (`preprocessing.split`) happens on the raw frame before any fitting. All
stateful preprocessing is placed inside one scikit-learn `Pipeline` together with the
estimator, so `fit` sees only the training partition and fitted preprocessing is persisted
with the model. Tests assert this (for example, scaler statistics equal the training-only
statistics).

### 4. Run manifests separate smoke runs from research runs

Every run writes `manifest.json` with `kind ∈ {smoke, development, research}`,
`synthetic_data`, config hash, seed, data fingerprints and a software/git snapshot. Only
`kind = research` with `synthetic_data = false` can enter the portal's result index. The
portal enforces this with a Zod schema, so an invalid index fails the build.

### 5. CLI via Typer

`driftguard` exposes `version`, `env`, `validate-config`, `synth` and `smoke` in M0.
Later milestones add dataset, train, evaluate, drift and benchmark commands.

### 6. Separate frontend application

`apps/research-portal/` is an independent Next.js (App Router, TypeScript, Tailwind CSS
v4, Recharts) project with its own lockfile and CI job. It is deployable to Vercel
without the Python toolchain and reads only versioned JSON under `src/data/results/`.
Pages are statically prerendered. The planned inference integration (M8) uses a
server-side route handler as the only caller of the Hugging Face Space, holding the token
server-side and validating input schema and size before forwarding.

### 7. Drift statistics: explicit implementations first

M5 will implement Population Stability Index (PSI) and two-sample Kolmogorov–Smirnov
tests directly on NumPy/SciPy, with fixed binning rules and thresholds calibrated on
training/validation data. These are short, deterministic and easy to audit. Third-party
drift libraries (candidates to assess include `river`, `frouros`, `alibi-detect` and
`evidently`) will be considered only after checking license, maintenance activity, Python
3.11 support, dependency weight and determinism. That evaluation is recorded as a
separate ADR in M5. **No drift library is a dependency in M0.**

### 8. Toolchain

- Python 3.11 is the primary tested version (`requires-python = ">=3.11,<3.13"`).
  `requirements/constraints-py311.txt` pins the exact tested set, and CI installs with it.
- Ruff (lint and format), mypy `--strict` on `src/` and `scripts/`, pytest with coverage,
  pip-audit.
- Portal: ESLint (`eslint-config-next`), `tsc --noEmit`, Vitest, `next build`, npm audit.
  TypeScript is pinned to 5.9: TypeScript 7 (native port) was `latest` on npm at the time
  of writing, and Next.js integration with it was not verified.

## Consequences

- Heavy dependencies (LightGBM, SHAP) are installed even for light tasks. SHAP is an
  optional extra (`.[explain]`).
- Only the pinned dependency set is tested. The lower bounds in `pyproject.toml` are
  declared minimums, not a tested matrix.
- The portal cannot show numbers until an exporter (M3) produces a research-kind index.
  This is intentional.

## Alternatives considered

- **Hydra/OmegaConf for configuration.** Rejected for M0: more powerful than needed, and
  Pydantic gives stricter validation with less indirection.
- **Monorepo tooling (Nx/Turborepo).** Rejected: there are only two independent apps, and
  path-scoped CI jobs are sufficient.
- **A drift library from day one.** Deferred (§7) to avoid coupling the protocol to a
  library before its behaviour is audited.
