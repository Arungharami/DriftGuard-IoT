# M5 audit — 2026-09-23

**M5 research campaign is BLOCKED, not complete.** This branch delivers evaluation
primitives, synthetic integration checks, an interactive evidence inventory, and a
prospective protocol. It does not deliver real IoT/IIoT generalization findings.
Missing results are not negative results. No dataset, model or attack trace is published.

## Verified repository state

Audit commands: `git fetch origin --prune`, `git ls-remote --heads origin`,
`git log --all`, `gh pr list --state all`, and `gh pr view {1,2,3}`.
The initial working tree was clean. `main` contained only initialization files.

| Milestone | Verified head | Evidence | Actual status |
| --- | --- | --- | --- |
| main | `4b687db041dd1c6e69f5fcfc59da03f06346ddcf` | initial commit | no research implementation |
| M0 | `722648f8f3ee635b7536b9d9c35d28abd0357c96` | [draft #1](https://github.com/Arungharami/DriftGuard-IoT/pull/1) | scaffold and portal; four CI jobs successful |
| M1 | `1fcea757e0ae9ba4b6e83cb5b5025608aff04c1f` | [draft #2](https://github.com/Arungharami/DriftGuard-IoT/pull/2) | registry/acquisition/schema tooling; four CI jobs successful |
| M2 | `ca0c7a49d9c8d4389111db3d72115586b840c54b` | [draft #3](https://github.com/Arungharami/DriftGuard-IoT/pull/3) | five baselines and leakage-safe preprocessing; four CI jobs successful |
| M3 | absent from fetched refs and all PRs | empty research results index | benchmark CIs/exporter exit criteria not established |
| M4 | absent from fetched refs and all PRs | package drift/adaptation stubs | aligned schemas/rolling-origin exit criteria not established |

Branch `m5/generalization-audit` starts at the exact M2 head above. The PR is stacked
against M2 to expose only this work; no lower PR is merged. Remote CI evidence establishes
what checks ran, not scientific validity. M2's PR describes four non-reportable development
runs on a different machine; their artifacts are unavailable locally and those claims
were not independently reproduced. No numeric claim from that PR is promoted here.

The original roadmap's M5 concerned drift/adaptation only. The user's requested scope
also includes M3/M4/M6/M9 concerns; this audit keeps the original milestones intact.

## Dataset and schema blockers

The [machine-readable local inventory](evidence/m5/dataset-inventory.json) records the
actual scan. No real tables exist under this checkout's `data/raw` tree. Registry
license facts below are inherited evidence dated 2026-09-22, not a new legal opinion
or a claim that publisher terms were rechecked by this branch.

- **Edge-IIoTset:** registry records CC BY-NC-SA 4.0, confirmed ML table schema and
  fingerprint. Local file absent. Academic-use permission alone does not establish
  compatible cross-dataset features or authorize artifact redistribution.
- **TON_IoT:** registry records academic-use permission, but provisional schema and no
  fingerprint. Local file absent. M2 reports publisher SharePoint authentication blocking
  acquisition; M5 did not bypass it or use third-party mirrors.
- **WUSTL-IIOT-2021:** registry says academic use is `not_stated`. M2's assumption that
  research hosting suffices does not satisfy this task's explicit licensed-only constraint.
  M5 blocks it even if a matching file is later supplied. Obtain explicit permission
  and update the reviewed card before use.
- Edge's packet fields, WUSTL's Argus flow fields, and TON's Zeek flow fields are not
  interchangeable. Matching names, IP protocol numbers, or ports do not prove equivalent
  aggregation, units, direction, capture interval or label semantics. No valid shared
  schema is asserted or padded with zeros.
- Timestamp parsing, timezone, capture boundaries, session grouping, attack-family
  ontology and initial training label availability have not been validated.

`driftguard m5-audit --root data` rechecks inventory and exits **2** for the blocked
campaign. Inventory success would not certify value quality, semantic alignment,
chronology or scientific readiness. This release intentionally has no real-data campaign
runner or reportable-result exporter. It cannot promote booleans supplied in a config
into verified research evidence.

## Delivered / still required

| Area | Delivered | Required before research execution |
| --- | --- | --- |
| Transfer | source-only fit/predict primitive; overlap rejection | reviewed schema/label mappings and pair-specific runner |
| Drift | predict-before-release simulator; frozen/periodic/error-triggered controls | validated detector, timestamp/session audit, detection metrics, recalibration policy |
| Robustness | bounded random sensor-noise aggregate utility | physically valid independent feature whitelist and real-data campaign |
| Unknown attacks | family-exclusion guard; source-validation threshold and metrics | family ontology, holdouts, score/model selection and campaign runner |
| SHAP | actual optional TreeSHAP smoke, mean-absolute/top-k stability | real models, windows, class alignment, bootstrap stability uncertainty |
| Resources | warmed latency percentiles, CPU time and throughput | fresh-process peak RSS, fit cost, serialization and device comparison |
| Ablations | paired circular block-bootstrap macro-F1 differences | controlled multi-seed real campaign and component ablations |
| Portal | filterable blocked experiment inventory and milestone evidence | verified research export after prerequisites are met |

These limitations are displayed in the portal rather than hidden in a log.

## No deployment / publication

Branch-specific `git.deploymentEnabled: false` is present in both repository and portal
roots, covering the two plausible Vercel root configurations. This follows
[Vercel's Git configuration](https://vercel.com/docs/project-configuration/git-configuration).
No deploy CLI, deployment hook, merge, raw-data export, model publication, or operational
evasion tool is part of this work. Existing research-result schema and empty index remain
unchanged; audit evidence uses a separate strict schema rejecting numeric metrics and
reportability claims.
