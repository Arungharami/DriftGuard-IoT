# Literature matrix

**Purpose:** determine whether the proposed drift-triggered, resource-constrained IDS
strategy already exists in equivalent form, before any novelty claim is made.

**Status: targeted primary-source metadata/abstract review updated 2026-09-25.**
See `reference-review-2026-09-25.md`, `literature-review.md` and manuscript references [1–12].
The detailed comparison matrix below remains an incomplete historical M0 template;
it must not be treated as a completed systematic review.

## Search protocol

- **Databases.** IEEE Xplore, ACM Digital Library, Scopus, arXiv, Google Scholar.
- **Query blocks** (combined with AND):
  1. intrusion detection OR anomaly detection OR IDS;
  2. IoT OR IIoT OR "industrial control" OR edge;
  3. "concept drift" OR "data drift" OR "distribution shift" OR "domain shift" OR
     "dataset shift";
  4. (optional) adaptation OR retraining OR "online learning" OR "incremental learning";
  5. (optional) TON_IoT OR "WUSTL-IIOT" OR "Edge-IIoTset".
- **Window:** 2015 to present. Record the date each search is run.
- **Inclusion.** Peer-reviewed or widely cited preprints that evaluate drift detection
  and/or adaptation for network or IoT intrusion detection.
- **Log.** For each query, record the database, the query string, the date and the hit
  count. Screen title/abstract, then full text.

## Matrix

| # | Reference (verified) | Datasets | Drift type (feature / performance / label) | Detector | Adaptation trigger & action | Label delay modelled? | Chronological eval? | Cross-dataset? | Resource measured? | Relation to DriftGuard-IoT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Ismail, Dandan & Qushou (2025), IEEE Access, doi:10.1109/ACCESS.2025.3554083 — *reference study; full text review pending* | TON_IoT, WUSTL-IIOT-2021, Edge-IIoTset | — | — | — | — | — | — | — | Baseline source |

## Background to review (general drift literature)

Candidate foundational references to locate and verify: surveys of concept-drift
adaptation, error-rate-based detectors such as DDM, adaptive windowing such as ADWIN,
and PSI and two-sample KS as distributional tests. Add each one to the matrix only after
checking its primary source.

## Novelty assessment

*Not yet possible.* To be written after the search is complete, answering: which
combination of (feature-drift detection with train-calibrated thresholds, delayed-label
adaptation choosing among retain/recalibrate/retrain, periodic-retraining comparator,
resource measurement, IoT/IIoT cross-dataset evaluation) is, or is not, already reported.
