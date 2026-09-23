# ADR 0002: Dataset registry, provenance and acquisition policy

- **Status:** Accepted (M1)
- **Date:** 2026-09-22

## Context

The study uses TON_IoT, WUSTL-IIOT-2021 and Edge-IIoTset. Each has different publisher
terms, distribution channels and file layouts. Kaggle hosts many re-uploads of these
datasets with inconsistent license labels. Results must be traceable to exact source
files, and no raw data or credentials may enter Git.

## Decision

1. **Registry as package data.** One YAML card per dataset lives in
   `src/driftguard/data/catalog/` and is validated by Pydantic (`driftguard.data.registry`).
   A card records the publisher, homepage, license facts (with the primary-source URL, the
   check date and a verbatim excerpt), required citations, the acquisition route, and
   one or more table schemas.
2. **Unverified facts are explicit.** Schemas carry `schema_status: provisional` until a
   downloaded header has been validated. File fingerprints are `null` until the team
   records them in a reviewed PR. Nothing is filled in from memory or from mirrors.
3. **Column roles drive safety.** Every column has a role (`feature`, `label`,
   `attack_type`, `timestamp`, `identifier`, `payload`) and an optional `exclude_reason`.
   Identifier and payload columns are *private*: they are never candidate features by
   default and are never exposed in public outputs. Publisher-documented leaky columns,
   such as WUSTL's six "unique to the attacks" columns, are excluded along with the
   publisher's reason.
4. **Acquisition policy.**
   - **Edge-IIoTset:** Kaggle, because the upload is by the lead author (first-party),
     license `CC BY-NC-SA 4.0`, version 5.
   - **TON_IoT and WUSTL-IIOT-2021:** manual download from the publisher. Every Kaggle
     copy found on 2026-09-22 was a third-party re-upload, several carrying licenses (MIT,
     Apache-2.0, CC0, CC-BY) that contradict or exceed the publisher's terms. A re-uploader
     cannot grant those rights, so no mirror is approved. The schema rejects approving any
     non-first-party Kaggle source.
5. **Kaggle adapter safeguards** (`driftguard.data.kaggle`):
   - explicit `--accept-license`;
   - a check that credentials are present, without reading their values;
   - a live check against Kaggle's public metadata that aborts if the license changed;
   - argv-only subprocess calls (no shell);
   - inside the repository, downloads may only go under the git-ignored `data/`;
   - archive fingerprinting and zip extraction guarded against path traversal,
     symlinks and decompression bombs;
   - an `acquisition.json` provenance record with no credentials in it.
6. **Redistribution gate** (`driftguard.data.licensing`). Raw data is never redistributed.
   Derived artifacts are allowed only if *every* source card has a verified license with
   `derived_artifact_redistribution: permitted`. No card grants that today, so the gate
   blocks every release until a license review is completed and recorded.
7. **Deterministic development subsets** are stratified, order-preserving and identified
   by a hash of (source SHA-256, n, seed, stratify column, min_per_class).
8. **Quality reports** are descriptive source statistics: duplicates, conflicting labels,
   constant columns, missing and infinite values, class counts, timestamp validity and
   label-purity leakage indicators. They are written only under `data/reports/`
   (git-ignored).
9. **Portal catalog.** `driftguard data export-catalog` writes metadata only (no column
   names, no data) to the portal. A test fails if the committed copy drifts from the
   registry.

## Consequences

- The TON_IoT and WUSTL downloads need a manual step, which is documented in
  `docs/datasets.md` and printed by `driftguard data show`.
- Provisional schemas must be confirmed (`driftguard data validate`) before M2 relies on
  them. A header mismatch fails loudly instead of silently dropping columns.
- The `kaggle` CLI is an optional extra (`pip install -e .[kaggle]`) and is not installed
  in CI. The adapter is tested with an injected fake CLI and fake metadata.
