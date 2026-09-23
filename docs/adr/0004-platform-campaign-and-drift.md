# Campaign, uncertainty and detector decisions

Reuse M2 `run_experiment` and extend M5 `delayed_prequential`; no second model factory
or streaming loop. River ADWIN consumes each newly released prediction error exactly
once, in label-availability order. Prediction at a timestamp precedes same-time labels.
ADWIN is a library detector, not proof of real concept drift. Its delta is fixed from
source development; target labels only become eligible at their release time. The
optional refit row budget bounds training history; full input stream residency remains
required, so stream source size must still fit the configured host.

Reference: https://riverml.xyz/latest/api/drift/ADWIN/ (checked 2026-09-23).
False alarms and detection delay require independently annotated changes; no such
real-dataset annotations have yet passed audit.

Campaign checkpoints contain config/source/data identities and every output fingerprint.
Resume validates files, refuses changed inputs and never counts failures as successes.
Source identity covers all package Python files. Process interruption may leave an
exclusive lock; after confirming no process is running, manually remove that lock.

Per-run stratified intervals are conditional row-level bootstrap intervals, not capture
or device confidence intervals. Seed standard deviation is separately reported. M5's
paired block bootstrap remains the time-dependent contrast primitive. Public research
export additionally needs independent design review and redistribution permission;
v2 manifest reportability alone is insufficient.

Cross-domain numeric alignment requires an explicit review-linked semantic contract;
the software cannot establish physical equivalence. No approved real contract is supplied.
Strict time partitions also require disjoint capture/session IDs. No chronological claim
may use CSV row order as genuine event time.
