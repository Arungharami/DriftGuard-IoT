# Methodology and provenance of each step

Every step is classified as:

- **Reproduction (R).** Re-implements a step of the reference study.
- **Extension (E).** Independent work.
- **Proposal (P).** Designed but not yet implemented or evaluated.

The reference methodology was **verified from the full text on 2026-09-22**. See
[docs/reference-paper-verification.md](../docs/reference-paper-verification.md) for the
exact facts, the text–figure discrepancies and the leakage risks.

| Step | Class | Implementation status | Verified against paper |
| --- | --- | --- | --- |
| Datasets: TON_IoT Train_Test network (211,043 rows), WUSTL full table, Edge-IIoTset ML table | R | WUSTL and Edge-IIoTset official files downloaded, fingerprinted, schemas confirmed (M2); TON_IoT blocked (sign-in) | **Yes**: row/class counts equal Table 4 for WUSTL and Edge-IIoTset |
| Target: multi-class attack type | R | Implemented (`target: attack_type`) | Yes (Table 4) |
| MI universe = numeric columns | R | `paper_mi_universe` | Yes: equals Figs. 3 and 4 on official files; TON_IoT inferred from Fig. 2 |
| MI ≥ 0.1 selection | R (paper_faithful: full data) / E (leakage_safe: train only) | `MutualInformationSelector` | Yes (Sec. III-A) |
| SMOTE then RandomUnderSampler, proportional targets, random_state 42 | R (full data) / E (train only) | `proportional_resample`, `ProportionalResampler` | Yes (Sec. III-B, Table 4) |
| 70:30 split | R | Both protocols | Yes (Sec. III-B); stratification is not stated and is used only in leakage_safe |
| DT, RF, Bagging, LightGBM | R | `build_estimator`, library defaults | Model set yes; hyperparameters **not reported** by the paper |
| Stacking: DT + RF base, MLP final | R | `build_estimator("stacking")` | Yes (Sec. III-C) |
| Precision, Recall, Micro-F1, model size, training time | R | `classification_metrics`; manifest timings and artifact size | Yes (Sec. IV, Table 7) |
| Deduplication before split, split before any fitting | E | `leakage_safe` protocol | n/a (paper does neither) |
| Identifier/payload/export-artifact exclusion | E | Registry roles and `exclude_reason` | n/a (paper retains ports and IP-IDs, contradicting its own text) |
| Category canonicalisation ('0' vs '0.0') | E | `CategoricalCanonicalizer` | n/a |
| Post-split duplicate/leakage audit | E | `audit_leakage` (manifest) | n/a |
| Macro-F1, MCC, balanced accuracy, per-class recall, PR-AUC | E | `classification_metrics` | n/a |
| Bootstrap confidence intervals, multi-seed runs | E | Not started (M3) | n/a |
| Chronological and rolling-origin evaluation | E | Chronological holdout (M0); rolling-origin M4 | n/a |
| Cross-dataset evaluation (TON_IoT → WUSTL, Table 8 features) | R/E | Not started (M4) | Table 8 features recorded |
| Feature-drift detector, adaptation policy, comparators | P → E | Not started (M5) | n/a |
| Resource benchmarking beyond fit time and size | E | Not started (M6) | n/a |
| SHAP and feature-selection stability | E | Not started (M6) | n/a |

## Differences from the reference protocol (leakage_safe)

1. Exact duplicates on model-visible columns are removed before splitting.
2. The split happens before any fitting. MI, encoders, imputers and resampling are fitted
   on the training partition only, and the test partition keeps its original
   distribution.
3. Ports are candidate features (as in the paper's figures), but WUSTL's `sIpId`, `dIpId`,
   addresses and timestamps are excluded per the publisher. So are Edge-IIoTset's
   identifiers, payload fields and three label-encoding export artifacts.
4. Categorical columns are ordinal-encoded after canonicalisation. The paper's MI
   universe used numeric columns only.
5. The primary metric is macro-F1, not micro-F1, because micro-F1 equals accuracy in
   single-label multi-class problems and hides minority-class failures.
