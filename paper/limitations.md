# Limitations and threats to validity (living document)

## Current state (M2)

- Only bounded **development** runs on real data exist (subsets of WUSTL-IIOT-2021 and
  Edge-IIoTset). They are NON-REPORTABLE. Nothing in this repository is evidence for or
  against any research question.
- TON_IoT has not been obtained: the official UNSW link requires a Microsoft sign-in.
- The reference paper reports no hyperparameters. Library defaults are an assumption.
- The paper's order of operations is inferred from the order of Sec. III (feature
  selection, then resampling, then split). The text does not state it in one sentence.
- Dataset terms were checked on 2026-09-22 (`docs/datasets.md`). WUSTL-IIOT-2021 states
  no license, and Edge-IIoTset's additional IEEE DataPort terms were not checked on a
  primary page. No derived artifact may be released until a license review is done.
- WUSTL-IIOT-2021 and Edge-IIoTset (ML table) schemas are confirmed against official
  headers. TON_IoT and the Edge-IIoTset DNN table remain provisional.
- Only the pinned dependency set is tested, and only on Python 3.11.

## Anticipated threats

- **Construct validity.** Benchmark IDS datasets are produced in testbeds, and their
  attack distributions may not represent operational traffic.
- **Internal validity.** Duplicate rows and label-encoding features can inflate scores.
  Mitigated by the M2 audit, but near-duplicate detection is heuristic.
- **Temporal validity.** Timestamps may be synthetic, reset per capture, or not
  monotone. Chronological experiments run only when timestamps pass validation (M4).
- **Cross-dataset validity.** Feature alignment across datasets requires semantic
  mappings that may be lossy. Every mapping is documented.
- **Drift ground truth.** Natural drift in these datasets is not labelled. Injected
  shifts test the detector's mechanics but may not match real drift.
- **Resource measurements.** Results depend on hardware, BLAS/threads and the OS.
  They are reported for the reference machine and are not claimed as edge-device results
  unless measured on one.
- **Statistical conclusion validity.** Bootstrap CIs assume i.i.d. test samples, which
  is violated in time-ordered data, so a block bootstrap is used there. Several datasets
  and models create multiplicity, handled by pre-declared comparison families.

## Open development observations (M2, NON-REPORTABLE)

- On a bounded WUSTL subset, LightGBM under the paper-faithful protocol reached macro-F1
  0.25, against about 0.95 under leakage-safe preprocessing. This looks like a training
  failure (for example, numerical instability with very large unscaled values such as
  `IdleTime`), not a property of the method. M3 must investigate it before any
  LightGBM comparison is made.
- Fit times under leakage-safe include the in-pipeline MI estimation and resampling, so
  they are not comparable with paper-faithful fit times, which exclude them.
