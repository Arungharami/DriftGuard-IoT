"""Persisting a fitted pipeline (M2 exit criterion: "persisted pipelines").

A fitted pipeline bundles preprocessing and the model together (see
preprocessing/pipeline.py), so persisting it is what makes a run's predictions
reproducible from the artifact alone, without re-fitting anything. Saved artifacts are
never committed to the repository (see artifacts/README.md) and are identified by the
SHA-256 of the serialized file, the same provenance convention used for data
(reporting/provenance.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import joblib

from driftguard.reporting.provenance import sha256_file

if TYPE_CHECKING:
    from imblearn.pipeline import Pipeline as ImbPipeline
    from sklearn.pipeline import Pipeline


def save_pipeline(pipeline: Pipeline | ImbPipeline, path: str | Path) -> str:
    """Serialize a fitted pipeline with joblib and return the artifact's SHA-256."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)
    return sha256_file(path)


def load_pipeline(path: str | Path) -> Pipeline | ImbPipeline:
    return joblib.load(Path(path))
