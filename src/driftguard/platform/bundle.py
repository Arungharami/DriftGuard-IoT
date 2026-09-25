"""Local trusted model bundles. A digest proves integrity, not trust in a pickle producer."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driftguard.data.licensing import redistribution_decision
from driftguard.data.registry import get_dataset
from driftguard.models.persistence import load_verified_pipeline
from driftguard.platform.campaign import write_json
from driftguard.reporting.manifest import ExperimentManifest
from driftguard.reporting.provenance import sha256_file


def prepare_bundle(run_dir: Path, model_name: str, destination: Path) -> dict[str, Any]:
    manifest = ExperimentManifest.model_validate_json((run_dir / "manifest.json").read_text())
    record = next(m for m in manifest.models if m.name == model_name)
    if not record.artifact_path or not record.artifact_sha256:
        raise ValueError("model artifact absent")
    path = (run_dir / record.artifact_path).resolve()
    if not path.is_relative_to(run_dir.resolve()) or sha256_file(path) != record.artifact_sha256:
        raise ValueError("artifact path or fingerprint invalid")
    features = manifest.protocol_details["features_in"]
    if not features or len(features) != len(set(features)):
        raise ValueError("feature schema invalid")
    reasons = ["owner release approval required"]
    if manifest.synthetic_data:
        reasons.append("synthetic fixture, not a research model")
    else:
        card = get_dataset(manifest.dataset.dataset_id)
        if not set(features).issubset(card.table(manifest.dataset.table_id).feature_columns):
            raise ValueError("private/non-feature columns in inference contract")
        reasons.extend(redistribution_decision([card], "derived_artifact").reasons)
    if not manifest.reportable:
        reasons.append(manifest.reportability)
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(path, destination / "pipeline.joblib")
    shutil.copyfile(run_dir / "manifest.json", destination / "manifest.json")
    metrics = json.loads((run_dir / "metrics.json").read_text())["metrics"][model_name]
    model = load_verified_pipeline(destination / "pipeline.joblib", record.artifact_sha256)
    meta = {
        "schema_version": 1,
        "model_name": model_name,
        "model_version": record.artifact_sha256[:16],
        "sha256": record.artifact_sha256,
        "features": features,
        "numeric_features": manifest.protocol_details["numeric_columns"],
        "labels": [str(v) for v in model.classes_],
        "synthetic_data": manifest.synthetic_data,
        "source_manifest_sha256": sha256_file(destination / "manifest.json"),
        "metrics": metrics,
        "publication_allowed": False,
        "release_blockers": reasons,
    }
    write_json(destination / "bundle.json", meta)
    (destination / "README.md").write_text(
        "# DriftGuard-IoT local bundle\n\nNot approved for publication.\n\n"
        f"Version: `{meta['model_version']}`. Source run: `{manifest.run_id}`.\n\n"
        + "\n".join(f"- {reason}" for reason in reasons)
        + "\n\nContains fitted preprocessing and model; predictions are not security guarantees.\n"
        "Only load this pickle when its producer and the reference manifest are trusted.\n"
    )
    return meta


@dataclass(frozen=True)
class LoadedBundle:
    pipeline: Any
    metadata: dict[str, Any]
    dataset_sha256: str
    path: Path

    @property
    def model_sha256(self) -> str:
        return str(self.metadata["sha256"])

    @property
    def synthetic(self) -> bool:
        return bool(self.metadata["synthetic_data"])


def load_bundle(bundle: Path) -> LoadedBundle:
    """Verify the manifest and pipeline digests before unpickling a local bundle."""
    metadata = json.loads((bundle / "bundle.json").read_text())
    if sha256_file(bundle / "manifest.json") != metadata["source_manifest_sha256"]:
        raise ValueError("source manifest integrity failure")
    manifest = ExperimentManifest.model_validate_json((bundle / "manifest.json").read_text())
    pipeline = load_verified_pipeline(bundle / "pipeline.joblib", metadata["sha256"])
    return LoadedBundle(pipeline, metadata, manifest.dataset.source_sha256, bundle)
