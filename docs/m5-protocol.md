# M5 prospective experiment protocol

Status: planned real-data campaign; not a preregistration, executed campaign, or finding.
Commit and review the completed dataset-specific configuration before opening target
labels. Synthetic mechanics checks are explicitly non-reportable.

## Admission and provenance

Require explicit verified use permission, attribution and publisher source; verify the
entire local file SHA-256 against a reviewed dataset card. Reject provisional schemas,
ambiguous files, unresolved types, unapproved mirrors and missing timestamp evidence.
Never infer permission from a downloadable URL. Dataset release/model release permissions
remain separate from permission to conduct local academic analysis.

A reviewed mapping must specify each field's physical meaning, unit conversion,
packet/flow granularity, directionality, aggregation window, missing-value meaning and
source documentation for every participating table. No intersection-by-name fallback.
Label maps must distinguish normal, known attack families and genuinely withheld families.
If no scientifically defensible common representation exists, report the pair as blocked.

Required run evidence: clean source commit and tree state, canonical config and hash,
all input/card/mapping hashes, dataset acquisition version and license snapshot,
row/session split hashes and counts, timestamp ranges, class support, all random seeds,
full estimator/preprocessing parameters, package lock/environment, hardware/OS/thread
limits, command, UTC start/end, outputs and output hashes, warnings and failure records.
Do not reuse model artifacts whose training population cannot be proved. This branch's
smoke records config/data/module hashes and environment but is not a research manifest.

## Train/test isolation and transfer

Split by independent capture/session/device group as justified by the dataset. Purge
feature-identical duplicates across partitions regardless of labels; resolve conflicting
labels in a prespecified development-only audit. The primitive fails on overlaps so
callers cannot silently remove unfavorable target rows. Verify group overlap separately.
Fit imputation, encoding, scaling, feature selection, resampling, calibration and model
selection entirely within source training/development. Fit the entire pipeline again
inside each training fold. Do not fit preprocessing on an unlabeled target test set.

Freeze hyperparameters using source validation. For every admissible ordered pair A→B,
compare the frozen A-trained pipeline on B against its source holdout. Treat B→A as a
separate run. An in-domain B baseline requires its own independent B train/test split;
it must not expose B test labels to transfer-model selection. Report per-family support,
macro-F1, balanced accuracy, per-class precision/recall, confusion counts and appropriate
probabilistic metrics. Omit undefined metrics with a reason rather than replacing them
with a success score.

## Chronology, delayed labels, drift and adaptation

Parse verified event times to a documented common unit and timezone. Reject invalid or
unsorted timestamps, unjustified row-order clocks, equal-time split boundaries and session
crossings. Respect actual duration, not row number, for real streams. Initially train only
on labels available before evaluation begins. Hold all events at an identical timestamp
in one prediction group. Labels available at that instant remain unavailable until the
next group: strict `event_time < now` and `label_time < now`. The implemented simulator
uses these rules and logs every row released to every refit.

Prospective label-delay scenarios: 0, 60 and 300 seconds, plus no labels during evaluation;
adjust only using operational/source evidence before freezing the protocol. Compare
frozen, periodic and detector-triggered adaptation with identical source data, seeds,
label schedule, rolling windows and budgets. The implemented error trigger is only a
simple development comparator; it is not ADWIN, a validated detector, or drift ground
truth. A validated detector/library decision, no-drift false-alarm rate, detection delay,
missed changes and adaptation cost are still required. Attack onset alone does not prove
concept drift. Use documented capture shifts and independently defined changes; log
alarms that never receive confirmatory evidence.

## Unknown-attack recognition

Choose held-out families before fitting. Exclude each held-out family from training,
feature/parameter selection and threshold calibration. Audit all partitions with the
family-exclusion guard. Choose an uncertainty/anomaly score using source known-class
validation only. Calibrate a fixed 5% known false-rejection operating point; use strict
`score > threshold` and report tie behavior. Never adjust thresholds on unknown target
labels. Measure unknown-vs-known AUROC, unknown recall, known false rejection, coverage
and known-class performance jointly. Missing known/unknown classes make that evaluation
undefined. Confidence is not proof of recognition; include overconfident unknown failures.
Synthetic norm-score outliers in the smoke run validate mechanics only.

## Bounded offline defensive sensitivity

Use a frozen model with no network calls or traffic generation. Whitelist only continuous,
independent sensor measurements whose additive perturbations preserve physical semantics.
Exclude labels, IDs, timestamps, categorical flags, ports, protocol fields, counts and
coupled features unless a reviewed constraint-preserving transformation exists.

The implemented test makes exactly two prediction calls, with <=10,000 evaluation rows
and noise <=5% of the training IQR. Prespecify fractions 0, 0.01 and 0.05 and paired seeds;
use a source-validated subset selection plan. Retain original values outside training
range instead of clipping a target into the training distribution. No label-guided search,
gradients, optimized evasive samples, packet reconstruction or sample export. Report
clean/corrupted accuracy and disagreement, including no-change and degraded results.
This measurement-noise test is not adversarial robustness certification. Sensitivity CIs
and physically valid dataset-specific transforms remain future campaign work.

## SHAP and resources

Use actual [TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html)
with a fixed source-training background. Explain the same named output class and ordered
features across prespecified evaluation windows. Never substitute impurity importance and
label it SHAP. Report mean absolute attribution and top-k Jaccard; include all ties at the
boundary. Zero attribution is undefined. Feature ranking changes are descriptive and
may reflect population composition. Campaign work must add block-resampled attribution
uncertainty and separately control model changes versus population changes.

Resources: measure the full fitted pipeline with fixed threads, seeded batches and at
least 3 warmups/100 measured repetitions. Report batch size, p50/p95/p99 batch latency,
throughput, CPU time, training wall time, serialized bytes, cold-start separately and
fresh-process peak RSS. The current utility reports no RSS value because process-lifetime
RSS is not per-model peak memory. Device identity, OS and package versions are mandatory;
workstation measurements must not be presented as edge-device performance.

## Controlled ablations and uncertainty

Freeze at least five seeds (11, 23, 42, 71, 101) before the real campaign. Compare one
component at a time: frozen vs periodic vs detector updates, label delays, feature
selection on/off, resampling on/off, and fixed confidence rejection on/off. Keep evaluation
rows, fit budgets and unrelated parameters identical. All reported contrasts must name
exactly what changed. Record failed fits and incomplete cells; do not pick only the best
seed. Report seed variation separately from test-sample uncertainty.

The implemented CI is a paired circular moving-block percentile bootstrap (2,000
replicates by default, 95%) for candidate-minus-baseline macro-F1 with a fixed class
universe. Pair the same resampled indices across methods. Select the block duration/size
from source-validation dependence evidence, not test significance; uneven time sampling
requires a time/session-aware resampler beyond this primitive. Blocks crossing distinct
captures are prohibited. Independent-capture sampling may require hierarchical bootstrap.
The small synthetic smoke uses 200 replicates only for integration speed.

CIs condition on fitted models and do not capture training variability. With too few
independent blocks/captures, mark inference underpowered; two blocks is merely a software
minimum, not adequate research power. Prespecify primary comparisons, report all intervals
(including zero-crossing or negative effects), and use a reviewed multiplicity procedure
for confirmatory tests. No best-window selection or invented significance. Individual
metric CIs, hierarchical intervals, and multiplicity testing are not yet implemented.

## Reproduce available checks

```sh
python3.11 -m venv .venv
.venv/bin/pip install -e '.[dev,explain]' -c requirements/constraints-py311.txt
.venv/bin/driftguard m5-audit --root data  # exit 2 means campaign blocked
.venv/bin/driftguard m5-smoke --explain --output-dir experiments/runs/m5-smoke
.venv/bin/pytest -m 'not slow and not real_data'
```

Smoke JSON stays under ignored `experiments/`; only clearly labeled aggregate validation
provenance is committed. It is never ingested into the portal's research results index.
