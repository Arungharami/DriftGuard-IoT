# DriftGuard-IoT

**Trustworthy, drift-aware and resource-efficient intrusion detection across IoT and IIoT environments.**

> **Status: M1 (dataset registry).** No model has been trained on a real dataset. The repository
> contains **no research results**. Any metric printed by the smoke command is computed
> on synthetic data and is explicitly labelled as such.

## Scientific positioning

DriftGuard-IoT is an **independent reproduction and extension** of:

> Ismail, Dandan and Qushou (2025). *Intrusion Detection in IoT and IIoT: Comparing
> Lightweight Machine Learning Techniques Using TON_IoT, WUSTL-IIOT-2021, and
> EdgeIIoTset Datasets.* IEEE Access. DOI: [10.1109/ACCESS.2025.3554083](https://doi.org/10.1109/ACCESS.2025.3554083)

1. **Reproduction track.** Leakage-safe re-implementation of the five reference baselines
   (Decision Tree, Random Forest, Bagging, DT/RF/MLP Stacking, LightGBM) on the three
   datasets.
2. **Extension track.** A separately evaluated drift monitor and drift-triggered adaptation
   policy under chronological and cross-domain evaluation, with resource measurements.

No novelty is claimed until the literature matrix ([paper/literature-matrix.md](paper/literature-matrix.md))
is complete. No superiority is claimed until experiments are run and verified. See
[docs/scientific-protocol.md](docs/scientific-protocol.md).

### Research questions

| ID  | Question |
| --- | -------- |
| RQ1 | How do leakage-safe baselines perform across the three IoT/IIoT datasets? |
| RQ2 | How do their minority-class detection rates change under domain shift and chronological evaluation? |
| RQ3 | Can drift monitoring identify significant changes in input distributions without excessive false alarms? |
| RQ4 | Can a drift-triggered adaptation policy improve robustness compared with static models and simple periodic retraining? |
| RQ5 | What are the measured accuracy, latency, memory and throughput trade-offs? |
| RQ6 | How stable and interpretable are selected features across environments? |

## Repository layout

```
.github/workflows/     CI: lint, type-check, tests, dependency audit, frontend build, hygiene
configs/               YAML configs: datasets/, models/, experiments/ (validated by Pydantic)
data/                  Local-only dataset storage (git-ignored); see data/README.md
src/driftguard/        Python research package (src layout)
  data/ preprocessing/ models/ drift/ adaptation/ evaluation/
  explainability/ benchmark/ inference/ reporting/
tests/                 pytest suite — synthetic fixtures only
notebooks/             Colab notebooks (thin wrappers over package functions; M7)
scripts/               Repository tooling (e.g. hygiene checks)
experiments/           Run outputs (git-ignored except README)
artifacts/             Model/preprocessing artifacts (git-ignored except README)
docs/                  ADRs, scientific protocol, milestones, security policy
paper/                 Manuscript planning documents and literature matrix
apps/research-portal/  Next.js research portal (Vercel; M8)
apps/inference-space/  Hugging Face inference Space (M7)
```

Architecture rationale: [docs/adr/0001-project-architecture.md](docs/adr/0001-project-architecture.md).

## Quick start (development)

Requires Python 3.11 (primary tested version) and, for the portal, Node.js ≥ 20.

```bash
python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]" -c requirements/constraints-py311.txt

driftguard --help
driftguard validate-config configs/experiments/smoke-synthetic.yaml
driftguard smoke                     # synthetic end-to-end run; writes experiments/runs/<run_id>/
driftguard data list                 # dataset registry: license, acquisition, schema status

ruff check . && ruff format --check .
mypy
pytest
python scripts/check_repo_hygiene.py
```

Portal:

```bash
cd apps/research-portal
npm ci
npm run lint && npm run typecheck && npm test && npm run build
```

## Data policy

Raw datasets are **never** committed. They are acquired locally (manual download from the
publisher, or the Kaggle adapter for Edge-IIoTset's first-party upload) with the user's own
credentials, fingerprinted with SHA-256, and kept under `data/`, which is git-ignored. CI
uses synthetic fixtures only. See [docs/datasets.md](docs/datasets.md) and
[data/README.md](data/README.md).

## Milestones

See [docs/milestones.md](docs/milestones.md). Each milestone is delivered on its own
feature branch through a draft pull request.

## Security

Credentials (Kaggle, Hugging Face, Vercel) live only in provider secret stores or local
environment variables. See [SECURITY.md](SECURITY.md).

## Team

Arun Kumar Gharami, Shefatha Rabbany and Ankith Gajam (Florida Atlantic University).

## License

**Not yet chosen.** A code license, and the terms under which trained artifacts may be
redistributed (which depend on each dataset's license), are open decisions for the project
owner. Until a license is added, all rights are reserved by the authors.
