# Platform completion audit

Audited 2026-09-23. Integration base: `95647cf06162512c31d458cf772cf449cabe97dc`.
Sole checkout/branch owner: this Codex session; no delegated coding agents. No history
rewrites, merges, branch deletion or previous-work removal are authorized.

## Recovered state

PRs [#1](https://github.com/Arungharami/DriftGuard-IoT/pull/1),
[#2](https://github.com/Arungharami/DriftGuard-IoT/pull/2),
[#3](https://github.com/Arungharami/DriftGuard-IoT/pull/3), and
[#4](https://github.com/Arungharami/DriftGuard-IoT/pull/4) are open drafts. M3/M4 remain
absent from all fetched refs and all PRs. M5 head CI has four passing jobs. The previous
full local test run had 218 passes and 10 missing-data skips. See `docs/m5-audit.md` for
exact predecessor commits and `docs/evidence/m5/` for synthetic-only run evidence.

The M2 runner already supports full files, five models and versioned manifests; it must
be reused. M5 already supplies delayed-label simulation, paired block intervals, frozen
transfer, bounded noise tests, unknown-score calibration, SHAP and inference timings.
There are no executed Colab notebooks, released model, inference service, completed
manuscript or verified real research result in this checkout. Older portal roadmap
placeholders do not represent implementations.

## Findings requiring correction

1. M2 v2 reportability checks do not enforce license, actual schema/value validation,
   independent sampling or absence of residual cross-split feature duplicates. A v2
   `reportable` flag alone must never authorize publication.
2. `prepare_leakage_safe` retains conflicting-label feature duplicates and diagnoses
   overlap rather than eliminating it. Research admission must fail on that overlap.
3. Full-data runs have no resumable repeated-seed campaign controller. M3 was not delivered.
4. M4 lacks reviewed packet/flow semantic contracts and genuine timestamp/group evidence.
5. M5 error-triggered control is not a validated drift detector. Its primitives must be
   extended rather than copied into a second streaming implementation.
6. LightGBM's WUSTL/paper-faithful anomaly is only described in PR #3; original run
   artifacts/data are absent. Synthetic diagnostics cannot resolve that observation.
7. Public result entries do not yet resolve and authenticate a local manifest file.
8. Hosted-service credentials and release permissions are distinct from code readiness.

## External inventory

- No real dataset files in the repository data root; no alternate data-root environment
  configured. Kaggle credentials absent from checked standard locations/environment.
- TON_IoT official UNSW page rechecked: academic use with citation; official download
  may require Microsoft sign-in. Schema and fingerprint remain unverified locally.
- Edge registry: first-party Kaggle, CC BY-NC-SA 4.0; file absent.
- WUSTL registry: no explicit use/distribution permission; file absent. No mirror used.
- Hugging Face connector and local CLI identify `arun-gharami`. Connector scopes include
  repository read, not write. A local token exists; it is never displayed or committed.
- Vercel connector/CLI authenticated. Seven listed projects, none named DriftGuard; no
  matching deployment target has been approved. No target chosen from unrelated projects.
- GitHub environment API returned no configured environments/protection rules. A workflow
  referring to an environment is not itself evidence of reviewer protection.

## Dependency-ordered implementation plan

1. Dataset admission and provenance; research gates; publication checks that distrust v2.
2. Reuse M2 for repeated-seed resumable campaign execution, per-run uncertainty and failures.
3. Extend M5 delayed-label simulator with library detector and bounded adaptation;
   add reviewed-schema transfer and chronology guards; retain static/periodic comparators.
4. Build thin deterministic Colab notebooks and execute representative notebooks locally.
5. Prepare validated inference bundle/service, license-gated release tooling, private Hub
   scaffolds if existing credentials permit; publish no unapproved real model.
6. Complete responsive portal routes, evidence-linked comparisons, server-only inference
   integration, validation/rate limits and unavailable states.
7. Add CI documentation/notebook/integration checks and manually dispatched protected
   campaign/release/deployment workflows; never train expensively on ordinary pushes.
8. Draft all manuscript sections with verified citations and explicitly unavailable results;
   generate tables only through verified result export.
9. Validate end-to-end synthetic fixture, browser where tools work, security, full CI;
   deliver a draft integration PR and component-by-component acceptance report.

Real experiments, semantic mappings, original anomaly resolution, licensed model release,
remote Colab execution, preview target approval and final production authorization remain
external prerequisites. They must not be replaced by invented metrics or approvals.
