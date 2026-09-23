# M5 local validation — 2026-09-23

This is software-validation evidence, not research evidence. All existing tests are
preserved. No real-data campaign ran; no negative research finding is inferred from
missing data. The paired-bootstrap unit test explicitly retains a known negative delta.

Environment: macOS ARM64, Python 3.11.16, Node 22.22.1. Dependencies installed from the
repository constraints with `.[dev,explain]`. Homebrew `libomp` 23.1.1 was installed to
resolve the initial LightGBM import failure; no test was disabled to hide that failure.

| Check | Observed result |
| --- | --- |
| `pytest -q` full suite | 218 passed, 10 skipped, 6 warnings |
| New M5 suite | 23 passed |
| Real-data skips | all 10: missing local dataset files |
| Warnings | six existing bounded MLP non-convergence warnings; retained |
| `ruff check .` / `ruff format --check .` | pass; 91 formatted Python files |
| `mypy` | pass; 44 source files |
| `driftguard data export-catalog --check` | catalog unchanged and synchronized |
| `python scripts/check_repo_hygiene.py` | pass |
| M0 smoke | passes, original config hash prefix `cbcf8c5a` |
| `driftguard m5-audit --root data` | expected exit 2; all three datasets blocked |
| M5 smoke with actual SHAP | passes; explicitly synthetic/non-reportable |
| `pip-audit -r requirements/constraints-py311.txt` | no known vulnerabilities (including optional SHAP pins) |
| `pip-audit` installed environment | no known vulnerabilities; local private project not on PyPI and not audited by that service |
| Portal lint / typecheck | pass |
| Portal Vitest | 12 passed in 3 files |
| Portal production build | pass, including `/experiments` |
| `npm audit --audit-level=high` | zero vulnerabilities across all installed dependencies |
| Local HTTP `/experiments` | success; blocked status, area selector, audit title and empty research message rendered |
| Browser interaction/visual check | blocked: browser tool failed before executing with missing `sandboxPolicy`; two attempts |

The Next.js build warns about an unrelated parent-directory lockfile outside this Git
repository; it ignores that lockfile and builds successfully. It was not modified.
Browser click behavior and visual layout have not been verified. CI additionally executes
the actual SHAP smoke; optional SHAP dependencies are pinned and included in audits.
