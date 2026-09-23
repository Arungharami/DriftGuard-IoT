# Milestones

Each milestone is developed on its own branch (`mN/<slug>`) and delivered through a
draft pull request listing its summary, tests and limitations. A milestone is complete
only when CI passes and its exit criteria are verified. Merging, deployments and external
publication require explicit approval from the project owner.

| ID | Scope | Exit criteria |
| --- | --- | --- |
| **M0** | Repository initialisation, architecture, scientific protocol, CI | Package installs; smoke CLI runs; synthetic tests, lint, types, hygiene, audit and portal build pass in CI |
| M1 | Dataset registry, synthetic fixtures, Kaggle adapter, provenance | Registry and license manifests for 3 datasets; Kaggle download with user credentials; SHA-256 manifests; reproducible subsets |
| **M2** | Leakage-safe preprocessing; five configurable baselines | DT, RF, Bagging, DT/RF/MLP Stacking and LightGBM; train-only MI, SMOTE and undersampling; duplicate and leakage audit; persisted pipelines |
| M3 | Reproducible single-dataset benchmark and reporting | Bootstrap CIs; research-kind manifests; result exporter to the portal schema |
| M4 | Cross-dataset schema, chronological evaluation, domain shift | Aligned schema; timestamp validation; rolling-origin evaluation; cross-dataset pairs |
| M5 | Drift detector and adaptation policy | Independently evaluated detector; retain/recalibrate/retrain policy vs no adaptation and periodic retraining; drift-library ADR |
| M6 | Explainability and resource benchmarking | SHAP (optional), selection stability; size, RSS, CPU, latency percentiles, throughput |
| M7 | Colab workflows; verified Hugging Face artifacts | Thin notebooks with bounded dev samples and checkpoints; gated publication script; model cards; inference Space |
| M8 | Research portal and API integration | All pages data-driven; simulated vs recorded distinction; secured server route to the Space; PR preview deployments |
| M9 | Full experiment campaign, ablations, statistics | Pre-registered matrix executed; ablations; statistical tests |
| M10 | Manuscript and public release readiness | Paper drafted from verified artifacts; release checklist |

## Audited state (2026-09-23)

M0–M2 exist as stacked draft PRs, not merged milestones. No M3/M4 refs or PRs were
found. The expanded M5 request is **blocked for real-data execution**; see
[M5 audit](m5-audit.md) and [prospective protocol](m5-protocol.md). Passing synthetic
checks does not satisfy M5 research exit criteria.
