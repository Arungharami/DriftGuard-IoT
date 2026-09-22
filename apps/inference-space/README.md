# Inference Space (M7)

A separately deployed Hugging Face Space serving **evaluated** DriftGuard-IoT models.

Planned design:

- Loads a versioned model artifact **together with its matching fitted preprocessing
  pipeline** and the run manifest that produced it.
- Strict request schema (Pydantic): exact feature names and types, finite numeric ranges,
  maximum batch size, maximum request body size.
- No raw datasets, traces or private artifacts are bundled.
- Called only by the research portal's server-side route; the token is a Space secret.

Not implemented in M0.
