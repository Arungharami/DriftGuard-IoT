# Experiment matrix (pre-registration draft)

Status: **draft. No experiment in this matrix has been run.** The matrix is frozen
before M9, and later changes are listed with justification.

## E1: In-distribution baselines (RQ1)

| Factor | Levels |
| --- | --- |
| Dataset | TON_IoT, WUSTL-IIOT-2021, Edge-IIoTset |
| Model | DT, RF, Bagging, Stacking (DT/RF/MLP), LightGBM |
| Split | Primary: feature-group-isolated holdout; paper-faithful stratification is a separate reproduction track |
| Seeds | 11, 23, 42, 71, 101 (matches CampaignConfig and the study plan) |
| Primary metric | Macro-F1 with 95% bootstrap CI |

## E2: Temporal and domain shift (RQ2)

| Factor | Levels |
| --- | --- |
| Temporal | Chronological holdout and rolling-origin, on datasets whose timestamps pass validation (M4) |
| Cross-domain | Ordered pairs (A → B) over the aligned schema; which pairs are valid is decided in M4 |
| Focus | Per-class recall of minority attack classes; macro-F1 degradation relative to E1 |

## E3: Drift detection (RQ3)

| Factor | Levels |
| --- | --- |
| Statistic | PSI, two-sample KS (others only if justified in M5) |
| Window size | To be fixed from training data in M5 |
| Ground truth | Injected shifts on held-out streams; natural shifts where documented |
| Measures | Detection delay, false alerts on no-drift segments, missed drifts |

## E4: Adaptation (RQ4)

| Policy | Description |
| --- | --- |
| Static | No updates after initial training |
| Periodic | Retrain on a fixed schedule, with a label budget matched to the adaptive policy |
| Drift-triggered | Retain / recalibrate / retrain after an alert, once enough delayed labels are available |

Factors: label delay, label budget. Measures: post-adaptation macro-F1 and minority
recall over time, number of updates, adaptation cost.

## E5: Resources (RQ5)

All E1 models: serialized size, peak RSS, CPU time, latency p50/p95/p99 (single sample and
batch), throughput. Measured on a documented reference machine.

## E6: Features and explanations (RQ6)

Mutual-information rankings and SHAP (where supported) across datasets, splits and seeds.
Stability measured with Jaccard/Kuncheva indices of the top-k feature sets.

## Pre-declared comparison families

To be completed before M9: the list of hypotheses, tests and multiplicity corrections.
