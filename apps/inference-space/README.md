---
title: DriftGuard-IoT
sdk: docker
app_port: 7860
---

# DriftGuard-IoT inference service

Prepared FastAPI Docker Space; not a deployed or approved research model. The service
returns `503` until the operator configures a trusted local bundle and `INFERENCE_API_KEY`.
`POST /predict` accepts `{ "rows": [{ "feature": 1.0 }] }` with exactly the bundle's
features, at most 128 rows. `X-Inference-Key` credentials stay on servers. `/health` has no data.
No user-supplied pickle, remote URL or raw network trace is accepted.

Build the Dockerfile from the **repository root**, or use the release staging script to
copy only source, constraints, README, pyproject and app into a staging directory.
A restricted data/model directory must never be uploaded along with this app.

Local launch: `uvicorn driftguard.inference.service:create_app --factory --port 7860`
starts in unavailable mode. A reviewed deployment supplies its own mounted bundle via
`DRIFTGUARD_BUNDLE_DIR`; bundle hashes establish integrity, not trust in the producer.
Use a scoped server-side Hugging Face token for a private Space plus a separate
`INFERENCE_API_KEY` for application authentication. No public release is approved yet.
