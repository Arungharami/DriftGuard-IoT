# Security and data-handling policy

## Credentials

- Kaggle, Hugging Face and Vercel credentials live only in **provider secret stores**
  (GitHub Actions secrets, Vercel environment variables, Hugging Face Space secrets) or in
  a local, git-ignored `.env` / `~/.kaggle/kaggle.json`. They are never stored in the
  repository, notebooks, logs or result files.
- Use **least-privilege tokens**: a read-only Kaggle key; a fine-grained Hugging Face
  token scoped to this project's repositories; a Vercel token scoped to this project.
- CI in M0 needs **no secrets**. Workflows run with `permissions: contents: read`.
- The browser never receives an API token. The portal calls the inference Space only
  through a server-side route (M8).

## Blocked content

`scripts/check_repo_hygiene.py` runs in CI (and optionally as a pre-commit hook). It
rejects:

- environment files (`.env*`, except `.env.example`), key and credential files;
- archives (`.zip`, `.tar.gz`, `.7z`, …), packet captures and raw logs;
- tabular data (`.csv`, `.parquet`, …) outside `tests/fixtures/`;
- serialized models and arrays (`.pkl`, `.joblib`, `.onnx`, `.safetensors`, `.npy`, …);
- any file larger than 2 MiB.

`.gitignore` excludes `data/`, `experiments/`, `artifacts/` and virtual environments.

## Datasets

Original datasets remain subject to their publishers' licenses. This project does not
redistribute raw data or confidential traces. Only evaluated model artifacts whose
redistribution is compatible with the dataset licenses are published, and only after
explicit approval (M7).

## Inference endpoints

The inference Space and the portal API route will enforce a strict input schema, maximum
request body size, maximum batch size and rate limiting (M7/M8).

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository rather than a public
issue.
