"""M2 runner, manifests, persistence and reportability (synthetic data only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from typer.testing import CliRunner

from driftguard.cli import app
from driftguard.config import ExperimentConfig, load_experiment_config
from driftguard.data.fixtures import synthesize_table
from driftguard.data.registry import get_dataset
from driftguard.experiments import load_dataset, run_experiment
from driftguard.models.persistence import ArtifactIntegrityError, load_verified_pipeline
from driftguard.preprocessing.paper_protocol import EDGE_IIOTSET, PAPER_PROTOCOLS, WUSTL_IIOT_2021
from driftguard.reporting.manifest import ExperimentManifest, reportability_reasons

REPO = Path(__file__).resolve().parent.parent
FAST_MODELS = [
    {"name": "decision_tree", "params": {}},
    {"name": "random_forest", "params": {"n_estimators": 5}},
    {"name": "bagging", "params": {"n_estimators": 3}},
    {"name": "stacking", "params": {"cv": 2, "rf": {"n_estimators": 5}, "mlp": {"max_iter": 30}}},
    {"name": "lightgbm", "params": {"n_estimators": 10}},
]


def _synthetic_config(protocol: str = "leakage_safe", **pre: Any) -> ExperimentConfig:
    base = load_experiment_config(REPO / f"configs/experiments/m2-{protocol}-synthetic.yaml")
    raw = base.model_dump()
    raw["models"] = FAST_MODELS
    raw["dataset"]["synthetic"]["n_samples"] = 600
    raw["preprocessing"].update(pre)
    return ExperimentConfig.model_validate(raw)


@pytest.fixture(scope="module")
def leakage_safe_run(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    return run_experiment(_synthetic_config(), tmp_path_factory.mktemp("runs"))


def test_all_five_baselines_train_and_are_evaluated(leakage_safe_run: dict[str, Any]) -> None:
    metrics = leakage_safe_run["metrics"]
    assert set(metrics) == {"decision_tree", "random_forest", "bagging", "stacking", "lightgbm"}
    for m in metrics.values():
        assert 0.0 <= m["macro_f1"] <= 1.0
        assert m["n_samples"] == leakage_safe_run["n_test"]
        assert "pr_auc_per_class" in m
        assert sum(m["support_per_class"].values()) == m["n_samples"]


def test_synthetic_results_are_non_reportable(leakage_safe_run: dict[str, Any]) -> None:
    run_dir = Path(leakage_safe_run["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 2
    assert manifest["reportable"] is False
    assert manifest["reportability"].startswith("NON-REPORTABLE")
    assert "synthetic data" in manifest["reportability"]
    assert metrics["reportability"] == manifest["reportability"]
    assert manifest["synthetic_data"] is True


def test_manifest_records_protocol_and_train_only_fit(leakage_safe_run: dict[str, Any]) -> None:
    m: ExperimentManifest = leakage_safe_run["manifest"]
    assert m.protocol_details["fit_scope"] == "train partition only"
    assert m.protocol_details["leakage_audit"]["cross_partition_duplicate_rows"] == 0
    for record in m.models:
        assert record.preprocessing["mi_fit_rows"] == m.protocol_details["n_train"]
        assert record.params, "hyperparameters must be recorded"
        assert record.fit_seconds >= 0.0
    assert "not claims about other hardware" in m.measurement_note


def test_persisted_pipelines_verify_and_reproduce_predictions(
    leakage_safe_run: dict[str, Any],
) -> None:
    m: ExperimentManifest = leakage_safe_run["manifest"]
    run_dir = Path(leakage_safe_run["run_dir"])
    cfg = _synthetic_config()
    data = load_dataset(cfg.dataset, cfg.seed)
    sample = data.frame[data.numeric + data.categorical].head(20)
    for record in m.models:
        assert record.artifact_sha256 is not None and record.artifact_path is not None
        pipe = load_verified_pipeline(run_dir / record.artifact_path, record.artifact_sha256)
        assert len(pipe.predict(sample)) == 20


def test_tampered_artifact_is_refused(leakage_safe_run: dict[str, Any], tmp_path: Path) -> None:
    record = leakage_safe_run["manifest"].models[0]
    src = Path(leakage_safe_run["run_dir"]) / record.artifact_path
    tampered = tmp_path / "tampered.joblib"
    tampered.write_bytes(src.read_bytes() + b"\0")
    with pytest.raises(ArtifactIntegrityError, match="refusing"):
        load_verified_pipeline(tampered, record.artifact_sha256)


def test_runs_are_reproducible(tmp_path: Path) -> None:
    a = run_experiment(_synthetic_config(), tmp_path / "a", save_models=False)
    b = run_experiment(_synthetic_config(), tmp_path / "b", save_models=False)
    assert a["metrics"] == b["metrics"]


def test_paper_faithful_run_is_flagged(tmp_path: Path) -> None:
    result = run_experiment(_synthetic_config("paper_faithful"), tmp_path, save_models=False)
    m: ExperimentManifest = result["manifest"]
    assert "paper_faithful protocol has known test-set leakage" in m.reportability
    assert m.protocol_details["test_contains_synthetic_rows"] is True
    assert m.protocol_details["reference"]["doi"] == "10.1109/ACCESS.2025.3554083"


# --------------------------------------------------------------------------- reportability


def _reasons(**overrides: Any) -> list[str]:
    base: dict[str, Any] = {
        "kind": "research",
        "synthetic_data": False,
        "row_limit": None,
        "sha256_matches_registry": True,
        "protocol": "leakage_safe",
    }
    return reportability_reasons(**{**base, **overrides})


def test_only_full_verified_leakage_safe_research_runs_are_reportable() -> None:
    assert _reasons() == []
    assert _reasons(kind="development")
    assert _reasons(synthetic_data=True)
    assert _reasons(row_limit=1000)
    assert _reasons(sha256_matches_registry=None)
    assert _reasons(sha256_matches_registry=False)
    assert _reasons(protocol="paper_faithful")


def test_manifest_cannot_be_forced_reportable(leakage_safe_run: dict[str, Any]) -> None:
    raw = leakage_safe_run["manifest"].model_dump()
    raw["reportable"] = True
    with pytest.raises(ValueError, match="cannot be reportable"):
        ExperimentManifest.model_validate(raw)


def test_registry_run_with_unverified_file_is_non_reportable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file that does not match the card's SHA-256 can never produce a research result."""
    table = get_dataset("wustl_iiot_2021").table()
    raw_dir = tmp_path / "raw" / "wustl_iiot_2021"
    raw_dir.mkdir(parents=True)
    fake = synthesize_table(table, n=400, seed=0)
    fake["Traffic"] = np.where(fake["Target"] == 1, "DoS", "normal")
    fake.to_csv(raw_dir / table.filename, index=False)
    monkeypatch.setenv("DRIFTGUARD_DATA_ROOT", str(tmp_path))

    raw = _synthetic_config().model_dump()
    raw["dataset"] = {"name": "fake-wustl", "kind": "wustl_iiot_2021", "target": "attack_type"}
    cfg = ExperimentConfig.model_validate(raw)
    result = run_experiment(cfg, tmp_path / "runs", kind="research", save_models=False)
    m: ExperimentManifest = result["manifest"]
    assert m.dataset.sha256_matches_registry is False
    assert m.reportable is False
    assert "fingerprint not verified" in m.reportability
    # Publisher-documented leaky columns never reach the model.
    for leaky in ("sIpId", "dIpId", "SrcAddr", "StartTime"):
        assert leaky not in m.protocol_details["features_in"]


# --------------------------------------------------------------------------- paper facts


def test_paper_protocol_constants_match_the_verified_paper() -> None:
    assert len(WUSTL_IIOT_2021.figure_mi_features) == 43
    assert len(EDGE_IIOTSET.figure_mi_features) == 42
    assert WUSTL_IIOT_2021.original_rows == get_dataset("wustl_iiot_2021").table().n_rows
    assert EDGE_IIOTSET.original_rows == get_dataset("edge_iiotset").table().n_rows
    assert set(PAPER_PROTOCOLS) == {"ton_iot", "wustl_iiot_2021", "edge_iiotset"}
    for p in PAPER_PROTOCOLS.values():
        assert 0.3 < p.resample_ratio < 3.0


def test_train_cli_reports_non_reportable(tmp_path: Path) -> None:
    cfg = tmp_path / "exp.yaml"
    body = (REPO / "configs/experiments/m2-leakage_safe-synthetic.yaml").read_text(encoding="utf-8")
    body = body.replace("../datasets/", f"{(REPO / 'configs/datasets').as_posix()}/")
    body = body.replace("../models/", f"{(REPO / 'configs/models').as_posix()}/")
    cfg.write_text(body, encoding="utf-8")
    result = CliRunner().invoke(
        app,
        ["train", "--config", str(cfg), "--output-dir", str(tmp_path / "o"), "--no-save-models"],
    )
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("NON-REPORTABLE")
