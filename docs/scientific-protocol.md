# Scientific protocol

Version 0.1 (M0). This protocol is binding for all experiments. Changes are made by pull
request, and each change is noted in the changelog at the end of this file.

## 1. Positioning and claims policy

1. DriftGuard-IoT is an **independent reproduction and extension** of Ismail, Dandan and
   Qushou (2025), doi:10.1109/ACCESS.2025.3554083. It is not affiliated with the authors.
2. Every component is classified as one of:
   - **Reproduction.** Re-implementation of a step described in the reference paper.
   - **Extension.** Independent work not present in the reference paper.
   - **Proposal.** Designed but not implemented or not yet evaluated.

   The classification is recorded in `paper/methodology.md`.
3. **No novelty claim** is made until `paper/literature-matrix.md` documents a structured
   search showing the drift-aware strategy is not already published in equivalent form.
4. **No superiority claim** is made without pre-specified comparisons, confidence
   intervals and the statistical tests described in §7.
5. **No fabricated, illustrative or placeholder metrics** appear in official results, the
   portal, model cards or the manuscript. Synthetic-data runs are for software validation
   only.

## 2. Research questions

RQ1–RQ6 are listed in the [README](../README.md#research-questions). Each experiment
config states the RQ(s) it serves (from M3 onward).

## 3. Data handling and leakage prevention

1. **Provenance.** Each source file is fingerprinted with SHA-256 at retrieval time.
   Dataset version, source URL, license and citation are recorded in a manifest (M1).
2. **Split before fit.** Train/test partitioning is performed on the raw, de-duplicated
   table before fitting any encoder, scaler, imputer, feature selector (including mutual
   information) or resampler (including SMOTE and undersampling).
3. **Train-only fitting.** All stateful transformations are fitted on the training
   partition only, inside a single persisted pipeline. Resampling is applied to training
   folds only, never to validation or test data.
4. **Untouched test partitions.** Test data is used exactly once per pre-registered
   comparison. It is never used for hyperparameter tuning, threshold selection, drift
   calibration, early stopping or model updates.
5. **Duplicate and target-leakage audit** (M2). Exact and near-duplicate rows across
   train/test are counted and reported. Features that directly encode the label (for
   example attack-type columns, or identifiers that deterministically map to the label)
   are listed and excluded, and the exclusion is justified.
6. **Identifying features.** IP/MAC addresses, ports that act as host identifiers,
   timestamps used as raw features, and payload-derived identifiers are reviewed per
   dataset. They are excluded from models unless justified, and are always excluded from
   public explanations.

## 4. Evaluation designs

| Design | Purpose | Condition |
| --- | --- | --- |
| Stratified holdout (per dataset) | RQ1 baseline comparability with the reference study | Rows treated as exchangeable; stated as an assumption |
| Chronological holdout | RQ2 temporal generalisation | Only when timestamps are validated as meaningful and monotone (M4) |
| Rolling-origin evaluation | RQ2–RQ4 drift simulation | Same timestamp validity requirement |
| Cross-dataset (train A → test B) | RQ2 domain shift | Only over a documented aligned feature schema (M4) |

Simulation rule: at simulation time *t*, the system may read only data with timestamp
≤ *t*. Labels become available only after a configured **label delay**, so unsupervised
feature drift (label-free) and supervised performance drift (label-dependent) are
evaluated separately.

## 5. Drift detection and adaptation (extension track)

1. Drift statistics (PSI, two-sample KS, or others justified in M5) are computed per
   feature over sliding windows against a reference window from training data.
2. Alert thresholds are derived **only** from training/validation data (for example a
   high quantile of the statistic under no-drift resampling), fixed before test-time
   simulation.
3. The detector is evaluated independently of any adaptation. Measures: detection delay,
   number of false alerts per unit time on no-drift segments, and missed drifts, all on
   datasets with known or injected shift.
4. The adaptation policy chooses among **retain**, **recalibrate** or **retrain** only
   when an alert fires *and* enough delayed labels exist. It is compared against (a) no
   adaptation and (b) periodic retraining on a fixed schedule with matched label budget.
5. Adaptation cost (wall-clock time, labels consumed, number of updates) is reported
   alongside post-adaptation performance.

## 6. Metrics

- **Classification.** Macro-F1 (primary), micro-F1, per-class recall, MCC, balanced
  accuracy. PR-AUC is reported per class only when probability scores are available and
  the class has enough positives. Calibration is reported as expected calibration error
  and reliability diagrams.
- **Alarm behaviour.** False-positive rate on benign traffic; false drift-alert rate.
- **Resources** (M6). Serialized model size, peak RSS, CPU time, and single-sample and
  batch latency percentiles (p50/p95/p99) and throughput, measured with warm-up on a
  documented machine. Hardware and software are recorded in the manifest.

## 7. Statistical analysis

- 95% confidence intervals via non-parametric bootstrap over test samples (stratified by
  class, ≥ 1,000 resamples, fixed seed). Assumption: test rows are i.i.d. draws from the
  test distribution. For chronological data, a block bootstrap is used instead, and the
  block length is reported.
- Multi-seed variability (≥ 5 seeds) is reported for stochastic models.
- Paired model comparisons on the same test set use McNemar's test or paired bootstrap
  differences. Comparisons across datasets use the Friedman test with a Nemenyi or
  Holm-corrected post-hoc test. The family of comparisons is pre-declared in
  `paper/experiment-matrix.md`.
- Effect sizes are reported alongside p-values, and "significant" is used only in the
  statistical sense.

## 8. Reproducibility record

Every run writes a manifest with the run kind, config hash, seed, data fingerprints,
Python/package versions, platform, and git commit. A result may be published only if:

1. its manifest has `kind = "research"` and `synthetic_data = false`,
2. the git commit is reachable on the default branch or a tagged release, and
3. the data fingerprints match the registry entry for the stated dataset version.

## 9. Changelog

- 0.1 (2026-09-22): initial protocol (M0).
- 0.2 (2026-09-22): M2. Reference methodology verified (docs/reference-paper-verification.md);
  run manifests v2 enforce reportability (§8); exact duplicates on model-visible columns are
  removed before splitting (§3); numeric-looking categories are canonicalised to remove
  export artifacts.
