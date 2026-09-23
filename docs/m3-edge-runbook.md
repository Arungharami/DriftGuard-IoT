# M3 runbook: first real-data baseline (Edge-IIoTset)

Status as of 2026-09-23: **BLOCKED. The dataset file is absent.**
`ML-EdgeIIoT-dataset.csv` is not under `data/raw/edge_iiotset/` in any local checkout.
No real-data metric exists. Every command below was checked to fail closed (non-zero exit,
no outputs) while the file is missing.

## 1. Acquire the file (project owner)

Source: the publisher's own Kaggle upload (dataset owner Mohamed Amine Ferrag).
Licence: CC BY-NC-SA 4.0. Non-commercial use, attribution required, share-alike.
The raw data is never redistributed by this project.

Use **one** of these options.

- **Browser.** Sign in to Kaggle.
  1. Open <https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot>.
  2. Download only `Edge-IIoTset dataset/Selected dataset for ML and DL/ML-EdgeIIoT-dataset.csv`
     (about 82 MB; the full dataset is 11.2 GB).
  3. Place it at `data/raw/edge_iiotset/ML-EdgeIIoT-dataset.csv`.
- **CLI with your own Kaggle API token.**
  1. Create a token from your Kaggle account settings.
  2. Save it as `~/.kaggle/kaggle.json` with mode `600`.
  3. Run `driftguard data download edge_iiotset --accept-license`.

  Agents must not create, read or re-enable credential files.

Expected SHA-256: `53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a`, with
157,800 rows and 82,184,390 bytes.

## 2. Validation and admission (in order; stop at the first failure)

```bash
driftguard data fingerprint edge_iiotset                  # SHA-256 must match the registry
driftguard data validate edge_iiotset --nrows 157800      # full header, order and value types
pytest -m real_data                                       # 10 real-data tests; Edge ones must pass
driftguard data quality edge_iiotset --nrows 157800 --out-dir data/reports
python -c "from driftguard.config import load_experiment_config as l; \
from driftguard.platform.admission import admit_dataset as a; \
print(a(l('configs/experiments/m3-edge_iiotset-dt-lgbm-seed42.yaml').dataset))"
```

Record `conflicting_label_groups` and `feature_duplicate_rows` from the quality report.
The count uses the binary `Attack_label` over the registry feature columns.
The strict admission gate stays in place: a non-zero conflict count **blocks** admission
until §4 has been reviewed.

## 3. First baseline, then the campaign

```bash
driftguard train --config configs/experiments/m3-edge_iiotset-dt-lgbm-seed42.yaml \
  --kind research --output-dir experiments/runs/m3
# Reproducibility: repeat into a second directory and compare.
driftguard train --config configs/experiments/m3-edge_iiotset-dt-lgbm-seed42.yaml \
  --kind research --output-dir experiments/runs/m3-repeat
```

Check each item before accepting the run:

| Check | Where |
| --- | --- |
| Dataset SHA-256 equals the registry value; `rows_loaded` is 157800 | `manifest.json` → `dataset` |
| Code and config identity | `config_hash`, `environment` (Git commit, packages) |
| Split: `split.json` hash equals `split_record.file_sha256`; train and test disjoint | `protocol_details.split_record` |
| Every class appears in train and test; conflict counts recorded | `split_record.class_counts`, `conflicting_label_*` |
| Zero cross-partition feature duplicates | `protocol_details.leakage_audit` |
| Per-class precision, recall, F1, FPR and confusion matrix | `metrics.json` |
| Runtime: fit and predict seconds, artifact size (this machine only) | `manifest.json` → `models` |
| Reproducible: identical split hashes and metrics across both runs | diff of the two `metrics.json` files |

Only after that, run the resumable campaign (five models × five seeds, checkpointed):

```bash
driftguard campaign --config configs/experiments/platform-edge_iiotset-full.yaml \
  --output-dir experiments/campaigns/edge-full --research
```

Rules for the results:

- Failed cells are persisted as `failure.json` and must be reviewed, never dropped.
- `campaign.json` keeps `reportable: false` until independent design and licence reviews.
- Hugging Face publication and Vercel deployment stay blocked.

## 4. Proposed policy if conflict groups exist (DRAFT, not implemented)

Status: *proposed, requires owner review; version `conflict-policy/v1`.*

1. **Primary analysis.** Keep every record. Conflicting groups stay whole within one
   partition, which the group split already enforces. The admission gate records the
   conflict count instead of blocking, but only for a table whose conflict count and
   group-hash digest are pinned in a reviewed registry change. All other admission
   requirements (licence, SHA-256, schema, row count, labels, finite values) stay unchanged.
2. **Sensitivity analysis.** A second, separately named configuration excludes the
   conflicting groups. It is reported alongside the primary analysis, never instead of it.
3. **Reporting.** The paper states the conflict counts and the excluded row count. Results
   from the two analyses are shown side by side.

No records are removed and no gate is relaxed until this policy is approved and committed
as its own reviewed change.
