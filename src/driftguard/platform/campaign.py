"""Resumable per-model/per-seed M2 campaign with verified checkpoint files.

No expensive work at import, ordinary CI uses small synthetic fixtures only.
A checkpoint verifies all referenced files; changed code/config/data invalidate reuse.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from driftguard.config import ExperimentConfig, load_experiment_config
from driftguard.experiments import run_experiment
from driftguard.platform.admission import admit_dataset
from driftguard.reporting.provenance import environment_snapshot, sha256_file, utc_timestamp


class CampaignConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seeds: list[int] = Field(default_factory=lambda: [11, 23, 42, 71, 101], min_length=2)
    bootstrap_repeats: int = Field(default=2000, ge=100, le=10000)
    max_cells: int = Field(default=25, ge=1, le=500)
    research: bool = False

    @model_validator(mode="after")
    def unique_seeds(self) -> CampaignConfig:
        if len(set(self.seeds)) != len(self.seeds) or any(s < 0 for s in self.seeds):
            raise ValueError("seeds must be unique nonnegative integers")
        return self


def source_fingerprint() -> str:
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for file in sorted(root.rglob("*.py")):
        digest.update(file.relative_to(root).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temp.replace(path)


def run_campaign(
    experiment: ExperimentConfig,
    output: Path,
    campaign: CampaignConfig,
    *,
    data_root: Path | None = None,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".campaign.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        return _run(experiment, output, campaign, data_root)
    finally:
        lock.unlink()


def _run(
    experiment: ExperimentConfig, output: Path, campaign: CampaignConfig, data_root: Path | None
) -> dict[str, Any]:
    if len(campaign.seeds) * len(experiment.models) > campaign.max_cells:
        raise ValueError("campaign exceeds configured cell budget")
    evidence = admit_dataset(experiment.dataset, data_root)
    if campaign.research and (not experiment.dataset.is_registry or experiment.dataset.row_limit):
        raise ValueError("research campaign requires verified full real tables")
    code_hash = source_fingerprint()
    identity = {
        "experiment": experiment.model_dump(mode="json"),
        "campaign": campaign.model_dump(mode="json"),
        "source_sha256": code_hash,
        "data_sha256": evidence.get("source_sha256", "synthetic"),
    }
    identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError(
            "resume refused: config, source or dataset changed; use a new output directory"
        )
    write_json(identity_path, identity)
    cells = []
    for seed in campaign.seeds:
        for model in experiment.models:
            cell_id = f"{model.name}-seed-{seed}"
            checkpoint = output / cell_id / "checkpoint.json"
            if checkpoint.exists():
                cell = json.loads(checkpoint.read_text())
                if cell["identity_hash"] != identity_hash:
                    raise ValueError("checkpoint campaign identity mismatch")
                for filename, digest in cell["files"].items():
                    path = (checkpoint.parent / filename).resolve()
                    if (
                        not path.is_relative_to(checkpoint.parent.resolve())
                        or sha256_file(path) != digest
                    ):
                        raise ValueError("checkpoint file integrity failure")
                cells.append(cell)
                continue
            config = experiment.model_copy(update={"seed": seed, "models": [model]})
            try:
                result = run_experiment(
                    config,
                    checkpoint.parent,
                    kind="research" if campaign.research else "development",
                    data_root=data_root,
                    bootstrap_repeats=campaign.bootstrap_repeats,
                )
                run_dir = Path(result["run_dir"])
                files = {
                    p.relative_to(checkpoint.parent).as_posix(): sha256_file(p)
                    for p in sorted(run_dir.rglob("*"))
                    if p.is_file()
                }
                cell = {
                    "id": cell_id,
                    "status": "complete",
                    "identity_hash": identity_hash,
                    "files": files,
                    "metrics": result["metrics"],
                    "manifest": (run_dir / "manifest.json").relative_to(output).as_posix(),
                }
                write_json(checkpoint, cell)
            except (ValueError, RuntimeError, OSError) as exc:
                # Persist failures and continue the matrix, never silently omit poor fits.
                cell = {
                    "id": cell_id,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                    "identity_hash": identity_hash,
                }
                write_json(checkpoint.parent / "failure.json", cell)
            cells.append(cell)
    aggregate = {}
    for model in experiment.models:
        values = [
            c["metrics"][model.name]["macro_f1"]
            for c in cells
            if c["status"] == "complete" and c["id"].startswith(model.name + "-seed-")
        ]
        aggregate[model.name] = {
            "completed_seeds": len(values),
            "planned_seeds": len(campaign.seeds),
            "mean_macro_f1": float(np.mean(values)) if values else None,
            "seed_standard_deviation": float(np.std(values, ddof=1)) if len(values) > 1 else None,
        }
    report = {
        "schema_version": 3,
        "kind": "campaign",
        "created_at": utc_timestamp(),
        "identity_hash": identity_hash,
        "identity": identity,
        "admission": evidence,
        "environment": environment_snapshot(),
        "cells": cells,
        "aggregate": aggregate,
        "reportable": False,
        "publication_status": "requires independent design and license review",
        "notice": "Conditional row CIs do not establish independent capture generalization",
    }
    write_json(output / "campaign.json", report)
    return report


def campaign_from_file(
    config: Path,
    output: Path,
    *,
    seeds: list[int] | None = None,
    research: bool = False,
    repeats: int = 2000,
) -> dict[str, Any]:
    return run_campaign(
        load_experiment_config(config),
        output,
        CampaignConfig(
            seeds=seeds or [11, 23, 42, 71, 101], research=research, bootstrap_repeats=repeats
        ),
    )
