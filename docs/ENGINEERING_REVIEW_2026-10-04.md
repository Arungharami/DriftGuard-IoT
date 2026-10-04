# Engineering review — October 4, 2026

## Scope

Source review of `src/driftguard/streaming/worker.py`, event store, data sampling, worker tests, CI, and README. This review addresses a bounded correctness issue; it does not certify the entire application, rerun all research experiments, or establish production readiness.

## Finding and repair

`queue.Queue(0)` silently makes an unbounded queue; a zero rate silently disabled the limiter and negative/non-finite rates were accepted. A type-only model-bundle import also pulled training dependencies into worker startup.

Reject non-positive/non-integer queue sizes and invalid rate/burst values. Keep the model-bundle type import behind TYPE_CHECKING so an unavailable-model worker does not need the training stack to import.

## Verification

A local integration check instantiated a real SQLite EventStore: 8 invalid limit cases were rejected; a one-item queue dropped and counted overflow. Worker import passed without LightGBM. Added pytest regressions are included in existing CI.

All changed Python files were syntax-compiled. Package installation from this workspace is blocked, so full dependency-backed suites and production builds are not described as passed. GitHub checks on the pull request provide the remaining integration validation.

## Next implementation work

Acquire and fingerprint the authorized TON_IoT, WUSTL-IIoT and Edge-IIoT files, then run the real-data admission and campaign gates. Synthetic streaming tests establish software behavior only; they do not establish intrusion-detection effectiveness.

## Evidence boundary

No raw benchmark data, measured research results, corpus approval records, model releases or production deployments were changed. Any affected scientific output must be re-executed and linked to the accepted source commit before updating manuscript claims.
