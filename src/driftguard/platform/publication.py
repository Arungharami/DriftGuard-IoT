"""Review- and license-gated sanitized exports. No flags bypass dataset permissions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from driftguard.data.licensing import redistribution_decision
from driftguard.data.registry import get_dataset
from driftguard.platform.campaign import write_json
from driftguard.reporting.manifest import ExperimentManifest
from driftguard.reporting.provenance import sha256_file


class PublicationReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    metrics_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approval_reference: str = Field(pattern=r"^https://github.com/Arungharami/DriftGuard-IoT/")
    reviewer: str = Field(min_length=1)
    independent_sampling_evidence: str = Field(min_length=30)
    owner_approved: bool


def sanitized_export(run_dir: Path, review: PublicationReview) -> dict[str, Any]:
    if not review.owner_approved:
        raise ValueError("owner approval required")
    if sha256_file(run_dir / "manifest.json") != review.manifest_sha256:
        raise ValueError("review does not bind this manifest")
    if sha256_file(run_dir / "metrics.json") != review.metrics_sha256:
        raise ValueError("review does not bind these metrics")
    manifest = ExperimentManifest.model_validate_json((run_dir / "manifest.json").read_text())
    if not manifest.reportable or manifest.synthetic_data:
        raise ValueError("synthetic or nonreportable run cannot be exported")
    card = get_dataset(manifest.dataset.dataset_id)
    decision = redistribution_decision([card], "derived_artifact")
    if not decision.allowed:
        raise ValueError("; ".join(decision.reasons))
    if manifest.protocol_details["leakage_audit"]["cross_partition_duplicate_rows"]:
        raise ValueError("cross-partition leakage blocks publication")
    if not manifest.environment.get("git_commit"):
        raise ValueError("exact source commit required")
    metrics = json.loads((run_dir / "metrics.json").read_text())
    if metrics["run_id"] != manifest.run_id:
        raise ValueError("manifest/metrics run mismatch")
    # Explicit allowlist excludes filesystem paths, IPs, rows, fitted values and categories.
    return {
        "schema_version": 3,
        "kind": "research",
        "synthetic_data": False,
        "run_id": manifest.run_id,
        "config_hash": manifest.config_hash,
        "git_commit": manifest.environment["git_commit"],
        "dataset": card.id,
        "data_sha256": manifest.dataset.source_sha256,
        "source_manifest_sha256": review.manifest_sha256,
        "review": review.model_dump(),
        "models": {
            name: {
                key: value
                for key, value in values.items()
                if key in {"macro_f1", "micro_f1", "mcc", "balanced_accuracy", "macro_f1_ci"}
            }
            for name, values in metrics["metrics"].items()
        },
    }


def export_to_portal(run_dir: Path, review: PublicationReview, portal: Path) -> None:
    sanitized = sanitized_export(run_dir, review)
    run_id = sanitized["run_id"]
    if Path(run_id).name != run_id or not run_id:
        raise ValueError("invalid run identifier")
    serialized = json.dumps(sanitized, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    public_path = portal / "public/manifests" / f"{digest}.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(serialized)
    index_path = portal / "src/data/results/index.json"
    index = json.loads(index_path.read_text())
    for model, values in sanitized["models"].items():
        entry_id = f"{run_id}-{model}"
        if any(entry["id"] == entry_id for entry in index["results"]):
            raise ValueError("result already exported")
        index["results"].append(
            {
                "id": entry_id,
                "experiment": "reviewed baseline",
                "dataset": sanitized["dataset"],
                "model": model,
                "evaluation": "stratified_holdout",
                "metrics": {
                    key: value for key, value in values.items() if isinstance(value, int | float)
                },
                "confidence_intervals": {
                    "macro_f1": {
                        key: values["macro_f1_ci"][key] for key in ("low", "high", "level")
                    }
                },
                "provenance": {
                    "run_id": run_id,
                    "kind": "research",
                    "synthetic_data": False,
                    "config_hash": sanitized["config_hash"],
                    "git_commit": sanitized["git_commit"],
                    "data_fingerprints": {sanitized["dataset"]: sanitized["data_sha256"]},
                    "manifest_url": f"/manifests/{digest}.json",
                    "manifest_sha256": digest,
                },
            }
        )
    write_json(index_path, index)
