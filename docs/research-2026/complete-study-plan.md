# 2026 research-completion plan: DriftGuard-IoT
Status: PROSPECTIVE STUDY / IMPLEMENTATION PLAN, 2026-09-23. This plan is not experimental evidence.
Working title: **DriftGuard-IoT: Reproducible and Resource-Aware Evaluation of Drift-Triggered Adaptation for IoT/IIoT Intrusion Detection with Delayed Labels**.

## 1. Verified starting point and essential correction
PR #12 merged on 2026-09-23. The project has five baseline factories; train-only leakage-safe preprocessing; a feature-group-isolated split and verifiable split.json; registry and admission controls; a resumable five-seed campaign; M5 synthetic-evaluation primitives; a manuscript draft; and a Next.js portal. Its PR CI passed. No admitted real-data campaign has been executed. The dataset acquisition state in docs/datasets.md describes provenance work performed in an earlier environment; it is NOT proof that files are available on the current machine. Confirm local paths, byte hashes and access rights anew.

The paper must separate: reproduced baseline methods, already-published drift/adaptation methods, independently implemented extensions, and prospective but untested features. A website, GitHub automation and model hosting are reproducibility infrastructure, not scientific novelty. Current prior work includes adaptive LightGBM (Yang/Shami 2021), CDDIA with interpretation/adaptation (Xu et al. 2024), AEWAE online ensembles (Wu et al. 2025), and the 2025 constrained-IoT drift review. Read these before fixing any novelty claim; citations are in paper/references-2026.bib.

## 2. Falsifiable questions and planned contribution
- RQ0 reproduction: under an isolated and pre-specified protocol, what performance is achieved by DT, RF, Bagging, stacking and LightGBM relative to a separately labeled reproduction of Ismail et al. (2025)?
- RQ1: with defensible event timestamps and independent change windows, what are supervised error-drift detection delay, missed changes and false alarms? Differentiate distribution shift from concept drift; attack onset alone is not ground truth for concept drift.
- RQ2: under the SAME label-release schedule, labels consumed, training budget and test stream, how do frozen, fixed-period and ADWIN-triggered updates differ in macro-F1, benign false-positive rate, update cost and recovery delay?
- RQ3: do source-trained feature attributions remain stable across capture-verified windows and model versions? SHAP associations are not causal explanations of attacks.
- RQ4: can an offline-trained frozen model produce demonstrably correct predictions through a real MQTT ingestion system with measured end-to-end latency, CPU, RSS and duplicate-message handling on a named edge gateway?
- Optional RQ5: withheld attack-family recognition, selected and frozen before fitting, with known false-rejection, coverage, unknown recall and overconfident failures.

The central prospective contribution is an **auditable delayed-label, matched-budget and capture-aware comparison**, NOT the invention of ADWIN, SHAP, LightGBM or drift adaptation. If timestamps or independent change annotations do not exist, downgrade RQ1/RQ2 claims to controlled offline simulations and document the limitation.

## 3. Dataset admission and licensing
Priority: Edge-IIoTset first-party author upload; ML-EdgeIIoT-dataset.csv should be 157800 rows with registered SHA-256 53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a. Place it under ignored data/raw/edge_iiotset, or run the repository's authenticated downloader with user-managed credentials. Neither disabled local Kaggle credentials nor file absence is permission to bypass admission.

Next: original UNSW TON_IoT network Train_Test table, manually acquired and fingerprinted; align its semantic feature definitions and confirm the event clock. WUSTL-IIOT-2021 remains excluded from the licensed-only campaign while academic-use permission is unconfirmed, even if obtainable online. Dataset use, copying and redistribution are separate permissions; do not upload raw data to GitHub, Hugging Face or a public demo by default.

Before modeling: verify source URL/date and legal terms; hash every original file; validate complete schema, units and row count; quantify missing/infinite fields, label support, exact duplicates, conflicting-label groups, near-duplicates, capture/session identities and leakage-prone identifiers. Keep the admission gate strict until conflict counts are measured. Any permitted-conflict policy requires a reviewed design decision and sensitivity analysis, never silent removal of bad-looking examples.

## 4. Experiment contract
Stage A (admitted first dataset): complete full-file validation, real_data tests and a pre-registered one-seed DT/LightGBM test. Check split.json indices, original row hashes, training-only feature selection, all per-class metrics, confusion matrices, serialized model hashes and timing. No synthetic outputs are research findings.

Stage B (reproduction): execute 5 baseline models x 5 precommitted seeds [11,23,42,71,101]. Preserve every failed cell. Source only the complete admitted ML table for the paper's full-table protocol. Separately label any paper-faithful reproduction as leakage-risk and do not compare its scores as a valid held-out estimate.

Stage C (shift): use chronological evaluation ONLY if capture metadata support the asserted order. If only an ML table with no genuine timestamps is available, use a clearly named **controlled distribution-shift/replay study**; never call arbitrary row order a naturally evolving stream. Do not combine packet, Zeek-flow and Argus-flow data just because fields have similar names. Prepare and review a physical-unit, aggregation-window, directionality and label-taxonomy contract before transfer.

Stage D (drift): calibrate detector thresholds and periodic-update frequency on source development partitions only; keep target holdouts unopened. Use frozen, periodic and ADWIN-triggered methods on identical ordered examples. Reveal a label only after both its event time and configured availability time precede the next prediction; log actual releases. Pre-register label delays 0, 60, 300 seconds and never-during-evaluation if the clock and workflow justify them. Respect equal-time event groups. Report false alarms per no-drift duration, missed drift windows, detection delays, fit count, retraining seconds, and labels consumed.

Stage E (ablation): compare same-model feature selection enabled/disabled, adaptation enabled/disabled, drift detector choices, identical label budget and prediction batch size. Never change multiple factors and attribute differences to one. Calibrate probabilities on source-only development data when calibration is studied.

## 5. Primary metrics and uncertainty
Classification: macro-F1 and per-attack recall (primary), benign false-positive rate, balanced accuracy, MCC, confusion counts and class support; report undefined metrics explicitly. Streaming: prequential accuracy/F1 per time window, time-to-detection, drift false alarms per hour, adaptation latency, model staleness and unavailable-label duration. Resource: end-to-end p50/p95/p99 latency, throughput, cold start, warm inference, serialized size, process peak RSS, CPU time, and optional calibrated wall-meter energy on actual hardware.

Report the independent sampling unit (capture/session/device, not merely correlated rows). Show repeated-seed variability separately from class-stratified or grouped uncertainty. For temporal comparisons, a paired block bootstrap requires enough independent blocks and a justified block length. Prespecify comparisons and multiplicity handling before final test evaluation. Report negative results, aborted runs and uncertainty honestly.

## 6. Publication artifacts and release gates
All approved numbers flow from a single immutable run catalog: dataset SHA-256, dataset-card/version/license snapshot, git SHA, exact command and YAML config digest, seeds, split.json hash, model/pipeline hashes, execution host, OS, installed package lock, class labels, latency measurement protocol, output artifact digests and outcome status. The paper's tables, portal's benchmark view and Hugging Face model card use the SAME verified sanitized summary artifact. Distinguish statistical confidence intervals from training-seed variability.

The GitHub repository is the canonical implementation. Kaggle is the first-party acquisition surface and optional notebook execution, not permission to mirror copyrighted data. Hugging Face receives a safe model card, verified compatible pipeline and optional weights only after an explicit license/security review. The Vercel portal hosts the protocol, verified interactive figures, provenance, negative findings, live-demo status and downloadable manuscript. Unsupported sections show NOT MEASURED, BLOCKED or SIMULATED, never plausible invented scores.

## 7. Manuscript composition
1. Abstract containing question, actual datasets/protocol and measured results only once available.
2. Problem, why deployment drift matters and operational limitations.
3. Prior art and difference matrix: Ismail 2025, Yang/Shami 2021, Xu 2024, Wu 2025, Øren 2025, and ADWIN/River.
4. Dataset provenance, legal permission, capture-dependent split, duplicate/label-conflict analysis and leakage ablations.
5. Five-model benchmark and reproducibility manifest.
6. Valid temporal/delayed-label protocol and matched-budget adaptation policies.
7. Live MQTT demo separated into replay, lab traffic and actual hardware evidence tiers.
8. Ablations, per-class performance, uncertainty, resource/edge trade-offs and SHAP stability.
9. Threats to validity, negative findings, ethics and reproducibility statement.
10. Conclusions constrained to verified outcomes, references from references-2026.bib and artifact appendix.

Required figures: full device/gateway/MQTT/cloud architecture; provenance DAG; capture/split diagram; model-by-dataset performance with uncertainty; prequential performance/alarm timeline; matched-budget ablation; feature stability; latency distribution and resource Pareto chart. Tables should distinguish actual evidence from planned measurements.

## 8. Gated completion definition
Software complete requires clean reproducible install, Python lint/types/tests, portal tests/E2E/build, security and dependency checks, no secrets/large-data tracking, a documented demo that runs on synthetic fixtures offline, and saved command-level verification. Paper ready additionally requires admitted real data, frozen reviewed experimental protocol, complete baselines, comparators appropriate to verified timestamps, independently validated statistics, review of all claims, citations checked and advisor/co-author approval. A deployable demo does not itself satisfy paper readiness.

Do not modify or merge active worktrees, publish model weights, claim edge-device measurements from a workstation, or loosen a license/data admission gate to manufacture progress. Changes should be separate, reviewable draft PRs.
