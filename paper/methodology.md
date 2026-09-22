# Methodology and provenance of each step

Every step is classified as:

- **Reproduction (R).** Re-implements a step of the reference study.
- **Extension (E).** Independent work.
- **Proposal (P).** Designed but not yet implemented or evaluated.

"Verified against paper" means the step was checked against the published text of the
reference study. As of M0 **no step has been checked**. Pipeline details must be confirmed
against the paper before M2 closes, including which of mutual-information selection,
SMOTE and undersampling the paper uses and in what order.

| Step | Class | Implementation status | Verified against paper |
| --- | --- | --- | --- |
| Datasets: TON_IoT, WUSTL-IIOT-2021, Edge-IIoTset | R | Not started (M1) | No |
| Mutual-information feature selection (train-only) | R (to confirm) | Not started (M2) | No |
| SMOTE / undersampling (train-only) | R (to confirm) | Not started (M2) | No |
| Decision Tree baseline | R | Factory stub with DT only (M0); configurable in M2 | No |
| Random Forest, Bagging, DT/RF/MLP Stacking, LightGBM | R | Not started (M2) | No |
| Split-before-fit, persisted pipelines | E (protocol hardening) | Implemented for synthetic data (M0) | n/a |
| Duplicate and target-leakage audit | E | Not started (M2) | n/a |
| Bootstrap confidence intervals, multi-seed runs | E | Not started (M3) | n/a |
| Chronological and rolling-origin evaluation | E | Chronological holdout implemented (M0); rolling-origin M4 | n/a |
| Cross-dataset evaluation over an aligned schema | E | Not started (M4) | n/a |
| Feature-drift detector (PSI/KS, calibrated thresholds) | P → E | Not started (M5) | n/a |
| Adaptation policy (retain / recalibrate / retrain) | P → E | Not started (M5) | n/a |
| Periodic-retraining and no-adaptation comparators | E | Not started (M5) | n/a |
| Resource benchmarking | E (extends the paper's lightweight focus) | Not started (M6) | No |
| SHAP and feature-selection stability | E | Not started (M6) | n/a |

## Differences from the reference protocol

Recorded here as they are discovered, with justification. Known intentional differences
in M0: none yet confirmed. Expected differences, to be confirmed:

- Transformers and resamplers are fitted on training data only, whatever the reference
  paper's order of operations.
- Confidence intervals and multi-seed variance are reported.
