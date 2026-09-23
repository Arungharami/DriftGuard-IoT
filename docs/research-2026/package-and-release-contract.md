# Package maintenance and reproducibility contract (2026-09-23)
Status: REVIEW PLAN, not a claim that every listed gate is implemented. Preserve existing passing CI and lockfiles. Audit the live default branch before applying edits; the roadmap in docs/milestones.md includes historical status that is no longer current.

## 1. Preserve reproducibility before upgrades
Current checked package on the PR #12 branch is a Hatchling src-layout Python 3.11-first distribution with Typer CLI, Ruff, strict mypy, pytest, pinned Python constraints and a Next.js research portal with npm lockfile. Treat installed versions as a reproducible snapshot. "Modern" means audited and supported, not blindly changing every dependency to the newest major release. Python 3.12 and newer Next.js/React versions require their own compatibility matrix and a passing notebook/model serialization regression before a supported-version claim.

Set an upgrade policy: security patch PRs immediately if compatible, minor releases in tested batches, major Python/Next/React/TypeScript/ESLint/Pydantic updates separately with migration review. Dependabot alerts are input to triage, not proof that blindly merging the latest is safe. Freeze the research environment and generated dependency lock/hash alongside each accepted experimental campaign.

## 2. Publishable installation contract
On a clean machine/ephemeral CI runner: create Python 3.11 environment; install from the checked constraints; run CLI help and a tiny synthetic smoke; build both wheel and source distribution; install wheel into a new environment; verify entrypoint import and CLI; validate all included package data and exclude raw data, model weights, keys and development outputs. Add package metadata (scientific purpose, installation docs, authorship/affiliations), a reviewed code license and explicit public-release permission separately from data/model permissions. Retain the "Private :: Do Not Upload" classifier until the release review.

Each exact research run gets: Git commit and clean-dirty flag; Python, pip, platform, libc, CPU architecture and library versions; package wheel digest or lockfile hash; full config/seed; data and model SHA-256; environment variables affecting determinism (thread counts); UTC command transcript; hardware description; training/inference time and outcomes. If a source build is not deterministic, capture artifacts and execution provenance rather than claiming bit-for-bit reproducibility.

## 3. CI release candidate gates
- Python: install with constraints; Ruff lint+format; mypy strict; all mock/synthetic tests; docs and notebook checks; data and credential hygiene; dependency audit. Real dataset integration tests run only on an explicitly provisioned researcher machine or authorized private runner, not by downloading copyrighted datasets in public CI.
- Frontend: npm ci from committed lock; ESLint, TypeScript typecheck, unit tests, build, Playwright integration/accessibility checks, npm audit; inspect server-side access controls and secret handling.
- Packaging: wheel/sdist build and fresh-venv installation; public import surface test; all supported interpreter versions in a small matrix only after validated; lock consistency and license scanner; SBOM and artifact digest for release candidates.
- Integration: Docker Compose MQTT fixture job, broker auth and ACL checks, schema tests, QoS1 redelivery and inference failure handling; redact all test fixtures and logs.
- Governance: branch protection, required checks, CODEOWNERS, reviewed PR template, at least one human review for scientific protocol/permission changes, secret scanning, least-privilege CI permissions, SHA-pinned third-party GitHub Actions, dependency automation and protected environments for HF/Vercel publication.

## 4. Research evidence gates
Publication uses a one-way evidence pipeline. CI passing does not make a run scientifically reportable. Authorize each dataset first. Validate full-file SHA-256 and schema. Freeze protocols before target labels. Save immutable manifests, model and split hashes. Run full non-synthetic evaluation. Conduct an independent design, license, provenance and claim review. Only then export a sanitized verified result index to the Vercel portal and a Hugging Face model card. Keep results absent, NOT MEASURED or explicitly simulated until each gate is satisfied.

Never place Kaggle keys, HF tokens, Vercel tokens, TLS private keys or GitHub PATs in Git history. Use only environment/secret stores; test public artifact scans. Do not deserialize third-party untrusted pickle/joblib files. Review the fitted pipeline's included dependencies and inference input schema before model release. Isolate models and use hashes/digests to detect changed artifacts.

## 5. Research deliverables and maintenance calendar
Prioritize first admitted Edge-IIoTset single-seed DT/LightGBM -> full five-model five-seed benchmarks -> independent temporal-capture feasibility check -> matched-budget adaptation -> live tier-A replay -> optional actual gateway benchmark -> manuscript statistical/claim review -> reviewed HF/Vercel publication. Re-run security/package checks on each release candidate. Any update that changes models/preprocessing must produce NEW model versions and cannot quietly replace results already used in a paper.

Operational references: GitHub Actions supply-chain documentation, official Hatch/Python packaging guide, OASIS MQTT v5.0, NIST SP 800-82 Rev. 3 FINAL (2023). A Rev. 4 INITIAL PUBLIC DRAFT appeared on 2026-09-21; record it as a draft, not a superseding final standard.
