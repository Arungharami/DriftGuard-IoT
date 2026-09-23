"""Versioned experiment manifests (v2) with enforced reportability.

A result is *reportable* only if every condition below holds; otherwise the manifest
carries a NON-REPORTABLE reason, and so does every derived metrics file:

* ``kind == "research"`` (development and smoke runs never are);
* real data (``synthetic_data`` is false);
* the full table was used (no ``row_limit``);
* the source file's SHA-256 equals the fingerprint recorded in the dataset card;
* the ``leakage_safe`` protocol (``paper_faithful`` reproduces a leaky order of operations).

The model validator recomputes reportability, so a manifest cannot be hand-edited into a
reportable state that its own fields contradict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MANIFEST_VERSION: Literal[2] = 2
NON_REPORTABLE = "NON-REPORTABLE"

RunKind = Literal["smoke", "development", "research"]


class DatasetProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    table_id: str | None
    source_file: str | None
    source_sha256: str
    sha256_matches_registry: bool | None  # None: no reference fingerprint (e.g. synthetic)
    row_limit: int | None
    rows_loaded: int
    target: str


class ModelRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    estimator: str
    params: dict[str, Any]
    fit_seconds: float
    predict_seconds: float
    artifact_path: str | None
    artifact_sha256: str | None
    artifact_size_bytes: int | None
    preprocessing: dict[str, Any] = Field(default_factory=dict)


class ExperimentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: Literal[2] = MANIFEST_VERSION
    run_id: str
    kind: RunKind
    experiment: str
    config_hash: str
    config: dict[str, Any]
    seed: int
    created_at: str
    synthetic_data: bool
    protocol: Literal["leakage_safe", "paper_faithful"]
    protocol_details: dict[str, Any]
    dataset: DatasetProvenance
    models: list[ModelRecord]
    measurement_note: str
    environment: dict[str, Any]
    reportable: bool = False
    reportability: str = ""

    @model_validator(mode="after")
    def _enforce_reportability(self) -> ExperimentManifest:
        reasons = reportability_reasons(
            kind=self.kind,
            synthetic_data=self.synthetic_data,
            row_limit=self.dataset.row_limit,
            sha256_matches_registry=self.dataset.sha256_matches_registry,
            protocol=self.protocol,
        )
        if self.reportable and reasons:
            raise ValueError(f"manifest cannot be reportable: {'; '.join(reasons)}")
        self.reportable = not reasons
        self.reportability = (
            "REPORTABLE research result"
            if not reasons
            else f"{NON_REPORTABLE}: " + "; ".join(reasons)
        )
        return self

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(), indent=2, sort_keys=True), encoding="utf-8")
        return path


def reportability_reasons(
    *,
    kind: str,
    synthetic_data: bool,
    row_limit: int | None,
    sha256_matches_registry: bool | None,
    protocol: str,
) -> list[str]:
    reasons: list[str] = []
    if synthetic_data:
        reasons.append("synthetic data")
    if kind != "research":
        reasons.append(f"{kind} run")
    if row_limit is not None:
        reasons.append(f"bounded development subset (row_limit={row_limit})")
    if sha256_matches_registry is not True:
        reasons.append("source fingerprint not verified against the dataset registry")
    if protocol != "leakage_safe":
        reasons.append(f"{protocol} protocol has known test-set leakage")
    return reasons
