"""Provenance capture: file fingerprints, software environment, and run manifests."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

TRACKED_PACKAGES: tuple[str, ...] = (
    "driftguard-iot",
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "imbalanced-learn",
    "lightgbm",
    "pydantic",
    "shap",
)

RunKind = Literal["smoke", "development", "research"]


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell, no user input
            [git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=5
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def environment_snapshot() -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": packages,
        "git_commit": _git_commit(),
    }


class RunManifest(BaseModel):
    """Everything needed to identify and reproduce one run.

    ``kind`` distinguishes smoke/development runs (never reportable) from research runs.
    Only ``research`` manifests may feed published results.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    kind: RunKind
    experiment: str
    config_hash: str
    seed: int
    created_at: str
    synthetic_data: bool
    data_fingerprints: dict[str, str]
    environment: dict[str, Any]
    notice: str

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(), indent=2, sort_keys=True), encoding="utf-8")
        return path


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
