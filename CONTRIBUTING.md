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
