"""Persisting a fitted pipeline (preprocessing and model in one artifact).

Artifacts are identified by the SHA-256 of the serialized file and are never committed
(see artifacts/README.md). joblib/pickle files can execute code when loaded, so
``load_verified_pipeline`` refuses any file whose hash differs from the one recorded in
the run manifest. Only load artifacts this project produced.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import joblib

from driftguard.reporting.provenance import sha256_file

if TYPE_CHECKING:
    from imblearn.pipeline import Pipeline as ImbPipeline
    from sklearn.pipeline import Pipeline


class ArtifactIntegrityError(RuntimeError):
    pass


def save_pipeline(pipeline: Pipeline | ImbPipeline | Any, path: str | Path) -> str:
    """Serialize a fitted pipeline with joblib and return the artifact's SHA-256."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path, compress=3)
    return sha256_file(path)


def load_pipeline(path: str | Path) -> Pipeline | ImbPipeline:
    """Load without verification. Prefer ``load_verified_pipeline``."""
    return joblib.load(Path(path))


def load_verified_pipeline(path: str | Path, expected_sha256: str) -> Pipeline | ImbPipeline:
    path = Path(path)
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ArtifactIntegrityError(
            f"{path.name}: SHA-256 {actual} does not match the manifest ({expected_sha256}); "
            "refusing to unpickle"
        )
    return joblib.load(path)
