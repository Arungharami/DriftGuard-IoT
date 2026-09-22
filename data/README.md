# Data

This directory is **local-only**. Everything here except this README is git-ignored and
blocked by the CI hygiene check.

Planned layout (created by the M1 tooling):

```
data/
  raw/<dataset>/<version>/        original downloads, unmodified
  manifests/<dataset>.json        source URL, version, license, citation, SHA-256 per file
  subsets/<dataset>/<subset-id>/  reproducible development samples (seeded)
```

## Datasets

The license, redistribution terms and citation requirements below are **not yet
verified**. M1 records them from the original publishers' pages, not from third-party
mirrors, before any data is used.

| Dataset | Original publisher | License / terms | Status |
| --- | --- | --- | --- |
| TON_IoT | UNSW Canberra Cyber | To be verified (M1) | Not downloaded |
| WUSTL-IIOT-2021 | Washington University in St. Louis | To be verified (M1) | Not downloaded |
| Edge-IIoTset | Dataset authors (see original publication) | To be verified (M1) | Not downloaded |

Kaggle mirrors may be used for versioned retrieval if their contents are fingerprinted
and their provenance to the original release is documented. Retrieval uses the user's own
Kaggle credentials (see `.env.example`); CI never downloads datasets.
