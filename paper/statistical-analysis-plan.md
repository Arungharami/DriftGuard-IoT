# Statistical analysis plan — draft before real-data admission

No real test outcomes have been observed. This specifies the analysis to review before
running the campaign; it does not assert that independent sampling units are available.

1. **Primary baseline endpoint:** macro-F1 on the identical feature-group-isolated test
   partition, all registered classes included. Start with the seed-42 DT and LightGBM
   configuration. The five-model campaign uses seeds 11, 23, 42, 71, 101 with identical
   per-seed split policy across models. Report every seed and failed cell, plus mean,
   standard deviation and range. Seeds are not independent network captures.
2. **Secondary endpoints:** per-class precision/recall/F1/support, balanced accuracy,
   MCC, benign false-positive rate and full confusion matrix; warm latency percentiles,
   serialized bytes and host context. Do not choose a winner from whichever secondary
   metric happens to be favorable. No test-based retuning or best-seed selection.
3. **Uncertainty:** current class-stratified bootstrap is conditional on the fitted model
   and observed class counts. Correlated captures require capture/group resampling,
   with the independent unit and power adequacy reviewed before inference. If those
   units cannot be established, report descriptive results without a confirmatory
   population claim. Overlapping repeated holdouts are not independent replications.
4. **Primary adaptation contrasts (a separate study):** delayed-label ADWIN policy minus
   frozen policy, and minus periodic retraining, at the same label/refit budget and on
   the same chronological observations. Freeze delay, window size, block duration and
   budget using source development data. Row order or artificial MQTT replay time is
   not admissible chronology. Output-mix MQTT alarms are not drift ground truth.
5. **Temporal uncertainty:** use the existing paired moving-block bootstrap only when
   its equal-spacing and within-capture assumptions hold; use 2,000 replicates and 95%
   intervals. Report effect direction, zero-crossing intervals, missed changes and
   unnecessary adaptations. Too few independent captures/blocks means underpowered,
   even if the software can compute an interval.
6. **Multiplicity:** for any confirmatory p-value analysis, pre-register the complete
   family of datasets, primary contrasts and alpha=0.05, with Holm adjustment applied
   across the full family. Do not manufacture p-values from percentile intervals. The
   current pipeline does not implement a reviewed confirmatory test, so claims of
   significance remain blocked until that method and its assumptions are reviewed.
7. **Sensitivity and failures:** preserve strict conflicting-label admission until
   actual counts and a pinned group digest are reviewed. Any approved exclude-conflict
   sensitivity analysis is separately named and compared with the primary policy.
   Record fit failures, incomplete cells, unusable timestamp evidence, domain-contract
   failures and negative outcomes without deleting them from the campaign denominator.
8. **Publication:** only validated, sanitized manifests admitted by the results gate may
   feed `scripts/render_research_tables.py` and portal charts. The current index is empty;
   no numeric research table or figure can be generated. A software pass, metadata
   review or model fingerprint does not substitute for independent design validation.

Execution details remain in `docs/m5-protocol.md`, `docs/m3-edge-runbook.md` and versioned
experiment configs. Final reviewers must record decisions, date and commit before test
labels are opened; subsequent deviations require a separate, dated justification.
