# Limitations and threats to validity (living document)

## Current state (M0)

- No experiments have been run on real data. Nothing in this repository is evidence for
  or against any research question.
- The reference paper's exact preprocessing order, hyperparameters and split ratios have
  not yet been checked against its text (see `methodology.md`).
- Dataset terms were checked on 2026-09-22 (`docs/datasets.md`). WUSTL-IIOT-2021 states
  no license, and Edge-IIoTset's additional IEEE DataPort terms were not checked on a
  primary page. No derived artifact may be released until a license review is done.
- All three table schemas are provisional until validated against downloaded headers.
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
