# Research integration audit — 2026-09-25

Engineering integration is reviewable; **real-data research and publication remain blocked**.
No PR was merged, model weights published, or production deployment created.

## Repository and integration

Fetched origin and inspected branches, worktrees, PRs and Actions. Latest main was
`e69ba85`. PRs #14 and #15 are on main; #16 was merged into
`fix/2026-sept-ci-compatibility` (`1e8342a`). A new sibling worktree
`DriftGuard-IoT-integration` and branch `integration/research-completion` started at
origin/main. Merging the dependency branch preserved #16 history, all streaming tests,
and reproducibility fixes, without conflicts. The original clean worktree at `e79e292`
and MQTT worktree at `091be0b` were preserved. No unrelated branch was rewritten.

Draft PR and final CI run: recorded below after the remote checks finish.

## CI and dependency repair

Main CI run `36034448815` failed with `typescript-eslint does not support TS 7.0`.
Restored an exact TypeScript 5.9.3 pin and regenerated the lockfile; retained Next.js
16.3.6, eslint-config-next 16.3.6, typescript-eslint 8.70.0 and ESLint 9.39.5.
The [typescript-eslint supported compiler range](https://typescript-eslint.io/users/dependency-versions/)
excludes TypeScript 7. Dependabot now excludes isolated compiler/ESLint major upgrades.
There is an upstream maintenance limitation: npm marks ESLint 9 deprecated, while the
current React/import plugins still declare support only through ESLint 9. This is a
compatible, tested restoration, not a claim that every upstream component has active
maintenance. A coordinated lint-stack migration remains necessary; forced peer overrides
were not used.

Local validation:

- Fresh Python 3.11 environment; editable installation of dev/explain/platform/notebooks/streaming extras with constraints; pip check passed.
- Ruff lint/format and mypy passed (71 source files).
- Pytest: 286 passed, 10 deselected, 85% coverage. These are software/synthetic checks.
- Dedicated real-Mosquitto test run: **8 passed, zero skipped**, covering authentication, ACLs, replay, duplicates, malformed/oversized packets, reconnect and TLS.
- pip-audit pinned set and npm audit (including dev dependencies): zero known vulnerabilities.
- Portal lint, typecheck, 21 unit tests and production build passed.
- Playwright: 10 passed across desktop/mobile, including axe accessibility, loading, connected/stale, disconnected and failure states.
- Documentation and notebook validation passed; three representative notebooks executed locally; M5 synthetic SHAP integration, catalog check and CLI smoke passed.
- Gitleaks full reachable Git history (`--all`, redacted): 30 commits scanned, no leaks. Final staged-file scan recorded below.

## Vercel — existing project retained and protected

The connected app listed seven unrelated projects and returned 404 for driftguard-iot.
The already-authenticated **CLI account did have access**, so no account action is needed
for this work. Connector visibility differs from CLI visibility and should not be used
to infer project absence.

- Team: `aruns-projects-ba93fc58`, `team_r62VZS6u8GtiCFAvauwwqo6B`.
- Project: `driftguard-iot`, `prj_uuEZYidwoSaF8nA9t57aCFJmv2P0`.
- Existing production: `dpl_APiUtSrTmRzZixfCssb4VwdFwubo`, source branch
  `m3/edge-real-baseline`, commit `ec98d3750109f9f3bbbb5faf05d31abd1b2605bd`.
- GitHub project link: **none**. This was a manually created deployment.
- Changed `ssoProtection.deploymentType` from `all_except_custom_domains` to `all`.
- Changed `gitProviderOptions.createDeployments` to `disabled`; repository Git deployment configs also disable automatic deployments. Manual reviewed previews remain possible.
- Anonymous requests to production `/`, `/demo`, `/api/inference`, and the deployment URL all returned 302 to Vercel SSO after protection. Before protection, `/` returned 200.
- Project, domain and existing production artifact retained. No production deploy performed.

Sanitized API state and anonymous checks: `docs/evidence/integration/vercel-protection.json`.
Vercel [documents the all-deployments setting](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication).
GitHub reports no configured environments; the existing controlled release workflow
therefore correctly remains gated. Before using it, configure preview/production
environments, required reviewers and the existing project/team IDs. Production settings
currently describe a generic root project; configure the Next.js app root/build settings
as part of the reviewed preview release, not an unreviewed production redeploy.

## Dataset and experiments — blocked at admission

No `ML-EdgeIIoT-dataset.csv` in the project parent tree (all three worktrees), Downloads,
or Kaggle cache. No DRIFTGUARD_DATA_ROOT override or active Kaggle environment credentials.
`~/.kaggle/kaggle.json.save` remains disabled and was neither read nor reactivated.
The first-party workflow confirmed CC BY-NC-SA 4.0 on the registered Kaggle author upload;
`driftguard data download edge_iiotset --accept-license` stopped with credentials missing.

Expected (registry, **not observed in this execution**): 157800 rows, SHA-256
`53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a`.
Actual checksum, schema, labels, duplicate/conflicting-label counts and scientific
admission remain unmeasured. The strict conflict gate is unchanged. The first full-data
DT/LightGBM run, five-model/five-seed campaign, genuine held-out MQTT replay and real-data
metrics were not run. No fabricated results, confusion matrices or research figures exist.

The first baseline and campaign runbook remains `docs/m3-edge-runbook.md`. Once active
credentials or the official file are provided, fingerprint/validate the entire file,
inspect conflict counts, review any proposed conflict policy, and only then run the
seed-42 DT/LightGBM configuration followed by seeds [11,23,42,71,101]. Keep hashes,
train-only preprocessing, per-class metrics, model size and measured host latency.
WUSTL licensing and TON_IoT schema/fingerprint prerequisites remain separate blockers.

## MQTT and portal

`/demo` now displays authenticated API aggregates through a server-side read-only proxy,
model digests, classifications, recent alerts, latency percentiles, retained-window
processing rate, duplicate/rejection/drop counts, evidence tier, and an uncalibrated
output-mix ADWIN warning. It links to the existing verified experiment explorer.
Requests use server-only credentials, HTTPS in production, fixed paths, no redirects,
timeouts, response-size bounds, schema filtering and no-store responses.

When offline, the portal displays the existing 2026-09-23 synthetic recording with its
source commit and measurement limits. It creates no invented alert rows. Live API
availability is distinguished from worker/broker health and stale prediction activity.
Producer replay rate and dataset fingerprint are not provided by the current live API;
the UI explicitly reports them unavailable instead of deriving unsupported values.
A richer authenticated telemetry contract and hosted private backend remain follow-ups.
Workstation latency is never presented as edge hardware performance; imposed replay time
is separate from original data time. Recorded/synthetic values are excluded from results.

Browser automation: the in-app browser failed to initialize (`sandboxPolicy` missing).
Playwright tests and the browser CLI were used; desktop/mobile screenshots were inspected
locally. No portal release was deployed. Synthetic full-chain verification is recorded
separately when available, never admitted as a research result.

## Manuscript and scientific limits

Manuscript now cites 12 relevant research references; primary publisher/author/institutional
records and publisher-deposited metadata were reviewed. See
`paper/reference-review-2026-09-25.md` for per-reference evidence and access limits.
IEEE full-text access was not available for every article; metadata/abstract review does
not establish full methodological validation. Existing prior full-text audit was preserved.
The paper separates the reproduction track, proposed delayed-label contribution and MQTT
output-mix demonstration. Added an explicit reproducibility statement and aligned the
experiment matrix with group-isolated partitions and existing campaign seeds.
The verified-results generator ran against zero admitted entries and produced no figure.
Independent methodological review, a frozen statistical comparison plan, broader novelty
review, licensed real-data evaluation, temporal annotations, semantic cross-domain mapping,
and physical hardware/resource measurements remain prerequisites to publication.
