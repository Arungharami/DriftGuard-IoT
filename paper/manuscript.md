# DriftGuard-IoT: An Evidence-Gated Platform for Drift-Aware, Explainable and Resource-Efficient Intrusion Detection

**Working manuscript — not submission ready. Real-data evaluation remains blocked.**

Arun Kumar Gharami (agharami2026@fau.edu), Shefatha Rabbany (srabbany2016@fau.edu),
Ankith Gajam (agajam2025@fau.edu)  
Grade 1 — CNT 6167 Internet of Things, Florida Atlantic University

## Abstract

Intrusion detection for Internet of Things and industrial Internet of Things environments
must account for changing traffic, delayed labels and constrained computation. We describe
DriftGuard-IoT, a reproducible research platform that separates dataset admission, model
selection, sequential evaluation and publication. Its implementation reuses five tree and
ensemble baselines, fits preprocessing within training partitions, supports repeated-seed
checkpoint recovery and evaluates frozen, periodic and detector-triggered policies under
explicit label-release schedules. Statistical and explanation utilities retain uncertainty
and provenance, while publication checks prevent synthetic validation from becoming
research evidence. The current contribution is an implemented experimental framework and
prospective protocol. Licensed local datasets, compatible cross-domain representations and
independent temporal annotations remain unavailable. Consequently, this manuscript reports
no real-data accuracy improvement, generalization result or operational resource claim.

*Index terms:* intrusion detection; IoT; IIoT; concept drift; delayed labels; reproducibility.

## I. Introduction

An IDS trained on historical network observations may encounter changed devices, workloads,
measurement procedures or attack behavior. Changes in an observed distribution do not
necessarily establish a change in the conditional relationship between features and labels.
Evaluation therefore needs both a clearly defined prediction task and independently justified
change annotations. Benchmark performance also depends on how captures, duplicates and
preprocessing are partitioned.

The comparison by Ismail, Dandan and Qushou [1] provides the baseline reference for this
project. DriftGuard preserves its reproduction protocol separately from a primary
leakage-safe protocol. The project asks whether adaptation improves performance relative
to frozen and periodic controls when access to labels, model selection and computational
budgets are equivalent. That hypothesis has not yet been tested on admitted real data.

## II. Related Work

Adaptive IoT analytics precedes this platform. Yang and Shami [2] propose optimized adaptive
and sliding windowing with LightGBM. Their work already combines a lightweight model with
concept-drift adaptation, so that combination cannot establish DriftGuard's novelty. Yang,
Manias and Shami [6] introduce a performance-weighted probability averaging ensemble for
adaptive IoT anomaly detection. Wu et al. [7] study online ensembles with drift-aware
components. These methods are relevant comparators, not baselines that this project can
claim to have reproduced.

ADWIN [5] maintains an adaptive observation window and detects changes in its monitored
statistic. DriftGuard uses the River implementation to monitor released prediction errors.
A detected error change is an alarm requiring interpretation; it is not automatically an
identified new attack or an independently confirmed concept change.

Edge-IIoTset [3] and TON_IoT [4] provide relevant benchmark contexts. Dataset diversity does
not itself imply compatible measurement semantics. Their use must respect publisher terms,
actual acquisition provenance and the distinction between packet and flow records. The
literature search is targeted rather than systematic: primary publisher/arXiv records were
queried for drift adaptation, online IDS, LightGBM, ADWIN and IoT. No claim of exhaustive
coverage is made. Verified metadata and the search scope are retained in
`docs/evidence/platform/bibliography.json` and `paper/literature-review.md`.

## III. Research Gap and Scope

The proposed contribution is an auditable evaluation of delayed-label adaptation under
strict isolation, combined with explanation and resource measurements. Whether that
assessment yields a novel scientific result depends on completed comparisons against prior
methods and on evidence of a substantive difference in setting or outcome. Integration of
GitHub, Colab, Hugging Face and Vercel is a systems contribution, not evidence of superior
detection performance.

Primary questions concern cross-domain degradation, adaptation relative to controls,
unknown-family recognition and the cost of maintaining performance. Secondary questions
concern feature stability and robustness to bounded measurement noise. No superiority,
state-of-the-art, causal explanation or operational-security claim is currently supported.

## IV. Proposed DriftGuard Method

The implementation first admits a source dataset using a reviewed registry card, explicit
use permission, an exact file fingerprint and actual schema/value validation. Candidate
features exclude labels, raw identifiers, timestamps and payloads. Deterministic partitions
precede imputation, categorical encoding, feature selection, resampling and model fitting.
The package contains Decision Tree, Random Forest, Bagging, DT/RF-to-MLP Stacking and
LightGBM factories inherited from the verified baseline implementation.

For sequential evaluation, an initial fitted model predicts an entire equal-timestamp group
before labels from that instant are released. A label is eligible for subsequent refitting
only after both its event time and availability time precede the next prediction time.
Frozen models never refit. Periodic models refit after a prespecified amount of newly
available supervision. The ADWIN policy monitors each newly released error once and
refits when its detector signals a change. An optional row budget bounds refit history.
Detector parameters and budgets must be selected on source development data.

Each run stores its model, preprocessing, input/config/source hashes and measurement
context. Campaign checkpoints are verified before reuse. Failed cells remain in the
campaign record. Publication requires additional license and design review; a successful
software run is insufficient authorization.

## V. Datasets and Experimental Setup

The intended datasets are TON_IoT, WUSTL-IIOT-2021 and Edge-IIoTset. This checkout has no
admitted real tables. Edge-IIoTset's first-party Kaggle license matches the registered
CC BY-NC-SA 4.0 value, but authenticated acquisition has not occurred here. TON_IoT's
publisher grants academic use with citation; its local schema/fingerprint remains
unverified. The WUSTL card records no explicit license, blocking the licensed-only campaign
and model release. Previously recorded fingerprints identify expected files, not files
observed in this execution.

The prospective campaign freezes seeds and model settings before evaluation. Real files
must be used in full where the protocol requires full-data training, subject to a declared
resource budget. CPU-only execution is supported. No GPU acceleration is claimed for
models that have not been configured and measured on a GPU. Private fields and raw data
remain outside repository artifacts and public notebooks.

## VI. Evaluation Protocol

Primary findings require leakage-safe partitions. Feature-identical conflicts, capture
or session overlap, unverified timestamps and target-informed model selection invalidate
research admission. For transfer, a reviewed contract must specify units, meaning,
granularity and transformations for each source/target feature. An unknown attack family
must be absent from training and threshold calibration. Chronological evaluations require
actual event time; row order is not an acceptable replacement.

Metrics include macro/micro F1, per-class recall, MCC, balanced accuracy, false-positive
rates and calibration. Resource measurements identify the pipeline, host, threads and
workload. Drift delay and false alarms are evaluated against externally supplied change
windows, rather than labels retrospectively chosen to agree with detector alarms.

Per-run class-stratified bootstrap intervals condition on observed class counts and a
fitted model. They do not correct capture dependence or quantify training variability.
Repeated-seed variation is reported separately. Paired moving-block bootstrap supports
prespecified temporal contrasts; block size needs source-validation evidence. A complete
real study must choose independent sampling units and a multiplicity plan before opening
held-out labels. See `docs/m5-protocol.md` for detailed assumptions and limitations.

## VII. Results

**No admitted real-data campaign has completed.** Software integration checks and synthetic
campaigns exercise code paths only. Their scores are deliberately excluded from the
manuscript's research-result tables. The absence of data is a blocker, not a negative
empirical result. No primary hypothesis can currently be accepted or rejected.

`paper/generated-results.md` is produced from the portal's verified result index only.
Every future numeric row must link to a content-addressed sanitized manifest. Failed,
negative and inconclusive experimental cells must remain visible. Reference-paper results
must be labeled as external findings and not copied into DriftGuard's result table.

## VIII. Cross-Domain Analysis

There is no verified cross-dataset estimate to interpret. Packet observations, Argus flows
and Zeek flows may encode different aggregation and directionality. Simple column renaming
could create an invalid experiment even if a model accepts the resulting matrix. The
platform requires a semantic contract and does not create one automatically. A valid
A-to-B experiment must hold B's test labels out of all selection and threshold decisions;
the reverse direction is a separate experiment with its own provenance.

## IX. Drift and Adaptation Analysis

The delayed-label simulator and ADWIN wiring are mechanically testable on synthetic
changes. Such checks do not establish sensitivity, false-alarm performance or label needs
on network captures. Real analysis will report missed changes, delay, false alarms, refit
cost, memory and predictive performance on the same timestamps across frozen, periodic
and adaptive methods. Detector and policy failures, including unnecessary refits and
performance degradation, remain outcomes rather than grounds to discard a seed.

## X. Explainability

TreeSHAP uses a fixed source-training background and the same output class across windows.
Mean absolute attributions and tie-aware top-k overlap describe ranking stability. They do
not establish causal attack mechanisms. Changes may result from population composition,
model updates or preprocessing differences; those factors require separate controls.
Attribution uncertainty and real-dataset window comparisons remain unverified.

## XI. Resource Efficiency

The platform measures warm batch latency percentiles, throughput, process CPU time,
serialized model size and fresh-process high-water RSS, with model load timing separated.
The measurement process includes library imports and loading, so RSS is a deployment
footprint measure rather than incremental tree memory. Schema-only synthetic batches are
instrumentation tests, not operational workloads. No inference about an edge device can
be drawn from this workstation without measurements on representative hardware.

## XII. Ablation Studies

Required controls isolate feature selection, leakage protection, detector behavior,
adaptation scheduling and calibration. Frozen, periodic and ADWIN policies share label
release schedules and source data. A paper-faithful comparison changes more than one
preprocessing decision and therefore cannot be presented as a single-factor leakage
ablation. Real ablations are blocked with the rest of the campaign. A calibration ablation
must fit calibration on source development folds, never on target test outcomes.

## XIII. Threats to Validity

Threats include acquisition bias, correlated flows, attack-specific capture artifacts,
conflicting labels, schema mismatch, source/target contamination, uncertain event clocks,
unrealistic delay assumptions, arbitrary detector tuning and multiple-comparison bias.
Fingerprint matching establishes byte identity, not dataset validity. Model hashes
establish integrity, not trust in an unpickling source. Dataset release permissions and
software licenses are separate. Public statistics may require review even when local
academic model fitting is permitted.

## XIV. Limitations

Data access and licensing currently prevent real experiments. The previously reported
WUSTL/paper-faithful LightGBM anomaly cannot be resolved without its original inputs and
run evidence. Synthetic diagnostics only test whether the implementation trains in a
controlled setting. Remote Colab execution is not established by local notebook execution.
A private Hugging Face repository is not a released model; a prepared Docker service is
not a deployed demonstration. Vercel production requires a confirmed target and explicit
owner authorization. Author review and a broader systematic literature comparison are
required before submission.

## XV. Conclusion

DriftGuard-IoT supplies an integrated experimental framework that keeps prediction-time
information, provenance and publication authority explicit. Its scientific value must
still be established through licensed, compatible and independently evaluated real data.
This draft documents the method and its testable hypotheses without presenting software
validation as evidence of improved intrusion detection.

## References

[1] S. Ismail, S. Dandan, and A. Qushou, “Intrusion Detection in IoT and IIoT: Comparing
Lightweight Machine Learning Techniques Using TON_IoT, WUSTL-IIOT-2021, and EdgeIIoTset
Datasets,” *IEEE Access*, vol. 13, pp. 73468–73485, 2025.
https://doi.org/10.1109/ACCESS.2025.3554083.

[2] L. Yang and A. Shami, “A Lightweight Concept Drift Detection and Adaptation Framework
for IoT Data Streams,” *IEEE Internet of Things Magazine*, vol. 4, no. 2, pp. 96–101, 2021.
https://doi.org/10.1109/IOTM.0001.2100012; author version https://arxiv.org/abs/2104.10529.

[3] M. A. Ferrag, O. Friha, D. Hamouda, L. Maglaras, and H. Janicke, “Edge-IIoTset: A New
Comprehensive Realistic Cyber Security Dataset of IoT and IIoT Applications for Centralized
and Federated Learning,” *IEEE Access*, vol. 10, pp. 40281–40306, 2022.
https://doi.org/10.1109/ACCESS.2022.3165809.

[4] A. Alsaedi, N. Moustafa, Z. Tari, A. Mahmood, and A. Anwar, “TON_IoT Telemetry Dataset:
A New Generation Dataset of IoT and IIoT for Data-Driven Intrusion Detection Systems,”
*IEEE Access*, vol. 8, pp. 165130–165150, 2020.
https://doi.org/10.1109/ACCESS.2020.3022862.

[5] A. Bifet and R. Gavaldà, “Learning from Time-Changing Data with Adaptive Windowing,”
*Proceedings of the 2007 SIAM International Conference on Data Mining*, pp. 443–448, 2007.
https://doi.org/10.1137/1.9781611972771.42.

[6] L. Yang, D. M. Manias, and A. Shami, “PWPAE: An Ensemble Framework for Concept Drift
Adaptation in IoT Data Streams,” author preprint, 2021. https://arxiv.org/abs/2109.05013.

[7] Y. Wu, L. Liu, Y. Yu, G. Chen, and J. Hu, “Online ensemble learning-based anomaly
detection for IoT systems,” *Applied Soft Computing*, vol. 173, article 112931, 2025.
https://doi.org/10.1016/j.asoc.2025.112931.
