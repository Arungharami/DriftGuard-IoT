"""Optional FastAPI service for an operator-approved, local, trusted bundle only."""

from __future__ import annotations

import math
import secrets
import time
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from driftguard.platform.bundle import load_bundle


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[dict[str, float | str]] = Field(min_length=1, max_length=128)


def create_app(bundle: Path | None = None, *, api_key: str | None = None) -> FastAPI:
    app = FastAPI(title="DriftGuard-IoT inference", docs_url=None, redoc_url=None)
    model, metadata = None, None
    if bundle is not None:
        loaded = load_bundle(bundle)
        model, metadata = loaded.pipeline, loaded.metadata

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ready" if model is not None and api_key else "unavailable"}

    @app.post("/predict")
    def predict(
        request: PredictRequest, x_inference_key: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        if model is None or metadata is None or not api_key:
            raise HTTPException(503, "No approved model configured")
        if not x_inference_key or not secrets.compare_digest(x_inference_key, api_key):
            raise HTTPException(401, "Authentication required")
        features = metadata["features"]
        for row in request.rows:
            if set(row) != set(features):
                raise HTTPException(422, "Feature schema mismatch")
            for name, value in row.items():
                if name in metadata["numeric_features"]:
                    if not isinstance(value, int | float) or not math.isfinite(value):
                        raise HTTPException(422, "Numeric features must be finite")
                elif not isinstance(value, str) or len(value) > 64:
                    raise HTTPException(422, "Invalid categorical value")
        started = time.perf_counter()
        try:
            labels = model.predict(pd.DataFrame(request.rows)[features])
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, "Input incompatible with model") from exc
        return {
            "predictions": [str(v) for v in labels],
            "model_version": metadata["model_version"],
            "synthetic_data": metadata["synthetic_data"],
            "latency_seconds": time.perf_counter() - started,
        }

    return app
