# Contributing

## Workflow

1. Create a branch per milestone or change: `mN/<slug>` (for example `m1/dataset-registry`).
2. Open a **draft** pull request early. Use the PR template and fill in the scientific
   classification, validation commands and limitations.
3. CI must pass before review. PR preview deployments of the portal are enabled from M8.
4. Merging, production deployment and external publication (Hugging Face, Vercel
   production, Kaggle) require explicit approval from the project owner.

Never force-push shared branches, delete others' branches, or rewrite history that
others may depend on.

## Local checks

```bash
ruff check . && ruff format --check .
mypy
pytest
python scripts/check_repo_hygiene.py
(cd apps/research-portal && npm run lint && npm run typecheck && npm test && npm run build)
```

## Research integrity

- Follow [docs/scientific-protocol.md](docs/scientific-protocol.md).
- Tests use synthetic fixtures only. Mark anything that needs a real dataset with
  `@pytest.mark.real_data`; such tests never run in CI.
- Do not commit raw data, trained artifacts or credentials (see [SECURITY.md](SECURITY.md)).

## Visitor and contributor entry points

Useful contributions to **DriftGuard-IoT** include:

- Improve a documented dataset adapter while preserving its feature and label contract.
- Reproduce a development check and report the exact configuration.
- Review leakage controls or explain an existing blocked input.

## Reporting a problem

Check existing issues first. Include the source commit or branch, environment, minimal steps, expected behavior, actual behavior, and a redacted error. State whether you used real data, an educational fixture, or exported results. Keep credentials and personal records out of public reports.

## Proposing a change

Choose one bounded task. Describe the intended behavior and how it will be checked before a large implementation. Use a focused branch and draft pull request; link any existing issue. Record exactly which checks ran, including failures and unavailable checks. Do not report a full suite as passed after running only a subset.

## Project evidence and boundaries

Retain real-data markers and NON-REPORTABLE development status. Follow the existing draft-PR and owner-approval workflow.

[Project overview and setup](README.md) · [Issues](https://github.com/Arungharami/DriftGuard-IoT/issues) · [Author's portfolio](https://arungharami.info)
