# Data

This directory is **local-only**. Everything here except this README is git-ignored and
blocked by the CI hygiene check.

```
data/
  raw/<dataset_id>/            original downloads (unmodified) + safely extracted archives
  manifests/<dataset_id>.json  SHA-256 fingerprints of every raw file
  reports/                     data-quality reports (descriptive, may contain private values)
  subsets/<dataset_id>/<id>/   deterministic development subsets + manifests
```

Dataset provenance, license terms, citations and schemas are defined in the registry
(`src/driftguard/data/catalog/*.yaml`). See [docs/datasets.md](../docs/datasets.md) for the
acquisition, fingerprinting, validation and quality workflow, and
[ADR 0002](../docs/adr/0002-dataset-registry-and-acquisition.md) for the policy.

| Dataset | License / terms (checked 2026-09-22) | Acquisition |
| --- | --- | --- |
| TON_IoT | Publisher terms: free academic use, commercial use by permission, 8 citations | Manual, from UNSW |
| WUSTL-IIOT-2021 | No license stated; citation requested | Manual, from WUSTL |
| Edge-IIoTset | CC BY-NC-SA 4.0 (first-party Kaggle upload) | `driftguard data download edge_iiotset --accept-license` |

Never commit anything from this directory, and never use unapproved third-party mirrors.
