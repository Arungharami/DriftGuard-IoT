# Continuation handoff

Recovery audit performed 2026-09-23 by a new session after the previous agent's context
ran out. Every statement below was checked against the repository, Git, GitHub and the
local machine on that date; nothing is carried over from summaries alone.
[`platform-completion-audit.md`](platform-completion-audit.md) is the previous (Codex)
session's audit. Where the two disagree, this document is newer.

## 1. Git and workspace state

| Item | Verified state |
| --- | --- |
| `origin/main` | `d73a37f`. Contains M0 → M1 → M2 → M5 through merges of PRs #1–#4 |
| PRs #1–#4 | **Merged** (stacked chain: #4→m2, #3→m1, #2→m0, #1→main). The previous audit's "open drafts" statement is out of date |
| PRs #5–#11 | Open Dependabot PRs. #8 (TypeScript 7), #9 (ESLint 10) and #11 (pydantic-core) fail CI. Not touched |
| CI on `origin/main` | Pass (run on `d73a37f`) |
| `integration/platform-completion` | Local only, never pushed, never CI-run: `34f646f` (audit doc) and `e79e292` (platform: admission gate, campaign runner, notebooks, portal pages, manuscript draft, release scripts). Written by a Codex session |
| This work | Branch `continuation/m3-real-baseline`, based on `e79e292`, in the separate worktree `../DriftGuard-IoT-continuation` |
| Other agents | Codex app-server processes were running on this machine during the audit. Only this worktree was written to. No auto-commit hooks are installed (`.git/hooks` contains only samples) |

`e79e292` is used as the base because the real-data path (`platform/admission.py`,
`platform/campaign.py`) exists only there. Its tests pass locally (232 passed, 10 skipped
before this change). This PR is the first time it goes through CI.

## 2. Milestone status (completion gates from the handoff brief)

| Milestone | Status | Evidence / gap |
| --- | --- | --- |
| M0 foundation | COMPLETE | Package, CLI, CI, portal skeleton; CI green on main |
| M1 dataset registry | PARTIAL | Registry, Kaggle adapter, fingerprints and schema validation exist. Only Edge-IIoTset `ml_edgeiiot` and WUSTL have confirmed schemas and SHA-256; TON_IoT is provisional |
| M2 baselines | PARTIAL | Five baselines, both protocols and v2 manifests work on synthetic data. No real-data run artifact exists anywhere |
| M3 full-data evaluation | PARTIAL (infrastructure only) | `platform/campaign.py`: resumable five-seed campaign with bootstrap CI and checkpoints. Never executed on real data |
| M4 drift / adaptation | NOT STARTED (research) | `adaptation/` is empty. `drift/assessment.py` scores alarms against given change windows. M5 `delayed_prequential` provides frozen, periodic and error-triggered comparators. No drift detector, no validated thresholds, no chronology evidence |
| M5 robustness | PARTIAL | Primitives implemented and tested. All outputs synthetic and NON-REPORTABLE |
| Colab notebooks | PARTIAL | 10 thin notebooks. Three execute locally in CI. Never run on Colab or real data |
| Hugging Face | BLOCKED | No admitted real model. The HF connector needs re-authorisation in this session. Release is gated on licence review |
| Vercel | BLOCKED | No approved target project. Portal build passing is not a deployment |
| Manuscript | PARTIAL | `paper/manuscript.md` structure and related work exist. Results sections correctly state results are unavailable |

## 3. Dataset availability and licensing (checked on this machine)

No dataset file is present in `data/raw/`, anywhere under `$HOME` (Spotlight and `find`),
or in `~/Downloads`. `~/.kaggle/` contains only `kaggle.json.save`, which is a disabled
credential. It was not read or activated.

| Dataset | Licence gate | Schema / fingerprint | File | Admissible? |
| --- | --- | --- | --- | --- |
| Edge-IIoTset `ml_edgeiiot` | CC BY-NC-SA 4.0, academic use permitted | Confirmed. SHA-256 `53101fad…3c1a`, 157,800 rows | **Absent** | Yes, once the file is present |
| WUSTL-IIOT-2021 | `academic_use: not_stated` | Confirmed, fingerprinted | Absent | **No**: `admit_dataset` requires explicit permission |
| TON_IoT `train_test_network` | Academic use permitted | Provisional, no SHA-256 | Absent | **No**: needs manual UNSW download and schema confirmation |

## 4. Gap closed in this change

Real IoT flow tables commonly contain rows with identical model-visible features but
different labels. The M2 leakage-safe split removed exact duplicates and then split rows
at random, so those conflicting rows could land on both sides. `run_experiment(kind="research")`
then aborts with "feature-identical rows cross the split". This finding is #2 in the
previous audit. The problem would most likely have stopped the first real-data research
run before any model was trained. The manifest also recorded no split membership.

Changes:

- `prepare_leakage_safe` assigns whole feature-identical groups to a single partition,
  stratified by each group's majority label. Cross-partition feature overlap is zero by
  construction, and a runtime guard checks it. The manifest now reports
  `split_strategy`, `feature_groups`, `conflicting_label_groups` and `conflicting_label_rows`.
- `run_experiment` writes `split.json` (train/test row indices of the loaded table). It
  also records the file hash, per-partition index hashes and per-class counts under
  `protocol_details.split_record`.
- The paper-faithful protocol is unchanged.
- `tests/test_group_split.py` covers conflict isolation, the 30% test fraction,
  determinism, seed sensitivity and verification of the split record.

## 5. Blockers requiring the project owner

1. **Edge-IIoTset file (blocks the first real experiment).** Choose one:
   - Place the official `ML-EdgeIIoT-dataset.csv` (SHA-256 `53101fad091af20bee815860962a5016b802ee45d456a141042f6183094c3c1a`)
     under `data/raw/edge_iiotset/`, or
   - Authorise use of Kaggle credentials (restore `~/.kaggle/kaggle.json`), then run
     `driftguard data download edge_iiotset --accept-license`.
2. **Admission conflict policy (decision needed).** `admit_dataset` rejects any table
   with conflicting-label feature groups (checked on the binary label). Because the split
   now isolates such groups, they are label noise rather than leakage. If Edge-IIoTset
   contains any such group, admission will block it. The options are to keep the strict
   gate, or to record the conflicts and admit the table. The code has not been changed;
   the owner should decide after seeing the real count.
3. **WUSTL-IIOT-2021 permission:** written permission from the publisher, or an explicit
   owner decision to record academic use as permitted.
4. **TON_IoT:** manual download from UNSW, then schema confirmation in a reviewed PR.
5. **Hugging Face:** re-authorise the claude.ai connector. **Vercel:** name the target project.

## 6. Dependency-ordered plan

1. *(done here)* Group-isolated split and split record.
2. Obtain Edge-IIoTset (blocker 1). Run `driftguard data validate` and the real-data
   tests (`pytest -m real_data`), then run `admit_dataset` and record its evidence.
3. Resolve blocker 2 using the actual conflict count.
4. Run a single-seed research run with DT and LightGBM, with the model configs cut down from
   `configs/experiments/platform-edge_iiotset-full.yaml`. Check the manifest, the split
   record, per-class metrics and resource timings.
5. Run the five-model × five-seed campaign (`driftguard campaign --research`) and export
   verified results to the portal schema.
6. M4: a chronology audit of `frame.time` in Edge-IIoTset (is the order genuine?). Then a
   drift detector with thresholds set on validation data only, plugged into
   `m5.evaluation.delayed_prequential` alongside the frozen, periodic and error-triggered
   comparators. Then ablations.
7. Integrations (Colab run, HF release, portal data, Vercel) once licences and targets allow.
8. Manuscript results generated only from exported artifacts.

## 7. Next exact action

Resolve blocker 1. Then run:

```bash
driftguard data validate edge_iiotset --nrows 157800   # full file; default reads 10,000 rows
pytest -m real_data
driftguard train --config <DT+LightGBM Edge config> --kind research
```
