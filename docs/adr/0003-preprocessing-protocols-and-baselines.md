# ADR 0003: Paper-faithful vs leakage-safe protocols, baselines and manifests

- **Status:** Accepted (M2)
- **Date:** 2026-09-22

## Context

The reference paper's methodology has now been verified from its full text
([reference-paper-verification.md](../reference-paper-verification.md)). Its order of
operations fits MI selection and SMOTE/undersampling on the full dataset before the
70:30 split. RQ1 needs a faithful reproduction *and* a leakage-safe re-evaluation, and the
difference between them must be attributable to the order of operations alone.

## Decision

1. **Two protocols, same components** (`driftguard.preprocessing.protocols`):
   - `paper_faithful`:
     1. numeric-dtype columns (the MI universe verified against Figs. 3–4);
     2. MI ≥ 0.1 fitted on **all rows**;
     3. proportional SMOTE + RandomUnderSampler (`random_state=42`) on **all rows**;
     4. 70:30 split.

     It records how many SMOTE rows reach the test set, and its manifest is always
     `NON-REPORTABLE`.
   - `leakage_safe`:
     1. deduplicate on model-visible columns;
     2. stratified 70:30 split;
     3. an `imblearn` pipeline fitted on **train only**: numeric coercion, category
        canonicalisation, median imputation, ordinal encoding, zero-variance removal,
        MI ≥ 0.1 and the same proportional resampling;
     4. the model.

     Resampling runs at fit time only.
2. **Resampling targets** follow the paper: per-class targets are
   `floor(total × class share)`, with `total = ratio × n`. The ratio defaults to the paper's
   Table 4 model-ready/original size, so bounded development runs scale consistently.
3. **Features** come from registry roles. Identifiers, payloads, timestamps and the attack
   type are never features. Columns with an `exclude_reason` are dropped, including the
   publisher-documented WUSTL leaks and the Edge-IIoTset export artifacts found in M2.
4. **Baselines** (`driftguard.models.factory`): DT, RF, Bagging, Stacking (DT + RF → MLP)
   and LightGBM, all with library defaults, because the paper reports none. The seed comes
   from the experiment config, and the full parameter set is recorded per model.
5. **Manifest v2** (`driftguard.reporting.manifest`): config and config hash; the source
   file's SHA-256 and whether it matches the registry; the row limit; protocol details
   (MI scores and selections, resampling counts, the duplicate/leakage audit); model
   parameters, timings and artifact SHA-256s; and the environment. A validator
   recomputes reportability. A result is reportable only for a `research` run on real,
   full, fingerprint-verified data with the `leakage_safe` protocol. Nothing in M2
   meets that bar.
6. **Persistence:** one joblib artifact per model (preprocessing and model together).
   Loading verifies its SHA-256 against the manifest before unpickling.
7. **Config hash stability:** fields added after M0 are omitted from the canonical hash
   while at their defaults, so M0 and M1 config hashes are unchanged.

## Integration note

A second agent session edited the same checkout during M2 (commit `ed492a68`). At the
owner's direction this session owns M2. That commit stays in history. Its persistence,
resource-timing and post-split leakage-audit modules and its factory, persistence and audit
tests were kept. Its top-k MI selection and SMOTETomek resampling were replaced, because
they contradict the verified paper protocol (MI threshold 0.1; SMOTE followed by
RandomUnderSampler).

## Consequences

- The paper-faithful metrics are expected to be inflated relative to leakage-safe ones.
  M3 quantifies this with confidence intervals on full data.
- Stacking with 5-fold CV over RF is the costliest baseline. Measured costs are
  machine-specific and recorded as such.
