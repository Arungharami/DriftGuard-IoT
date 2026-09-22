from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from driftguard import __version__
from driftguard.cli import app
from driftguard.config import ModelConfig, load_experiment_config
from driftguard.models.factory import build_estimator
from driftguard.smoke import SMOKE_NOTICE, run_smoke

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_env_command_reports_python_and_packages() -> None:
    result = runner.invoke(app, ["env"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["python"].startswith("3.")
    assert payload["packages"]["scikit-learn"] is not None


def test_validate_config_ok_and_invalid(repo_root: Path, tmp_path: Path) -> None:
    ok = runner.invoke(
        app, ["validate-config", str(repo_root / "configs/experiments/smoke-synthetic.yaml")]
    )
    assert ok.exit_code == 0, ok.output
    assert ok.stdout.startswith("OK:")

    bad = tmp_path / "bad.yaml"
    bad.write_text("name: Bad Name\n", encoding="utf-8")
    result = runner.invoke(app, ["validate-config", str(bad)])
    assert result.exit_code == 1


def test_synth_command_writes_csv(tmp_path: Path) -> None:
    out = tmp_path / "flows.csv"
    result = runner.invoke(app, ["synth", "--out", str(out), "--n-samples", "120"])
    assert result.exit_code == 0, result.output
    assert len(out.read_text(encoding="utf-8").splitlines()) == 121


@pytest.mark.parametrize(
    "config_name", ["smoke-synthetic.yaml", "smoke-synthetic-chronological.yaml"]
)
def test_run_smoke_writes_labelled_manifest(
    repo_root: Path, tmp_path: Path, config_name: str
) -> None:
    config = load_experiment_config(repo_root / "configs/experiments" / config_name)
    summary = run_smoke(config, tmp_path)

    run_dir = Path(summary["run_dir"])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))

    assert manifest["kind"] == "smoke"
    assert manifest["synthetic_data"] is True
    assert manifest["notice"] == SMOKE_NOTICE
    assert manifest["config_hash"] == config.canonical_hash()
    assert len(next(iter(manifest["data_fingerprints"].values()))) == 64
    assert metrics["kind"] == "smoke"

    # Target and time columns never reach the model.
    assert "label" not in summary["features"]
    assert "timestamp" not in summary["features"]
    dt = summary["metrics"]["decision_tree"]
    assert 0.0 <= dt["macro_f1"] <= 1.0
    assert set(dt["recall_per_class"]) == {"normal", "dos", "scan", "injection"}


def test_smoke_is_reproducible(repo_root: Path, tmp_path: Path) -> None:
    config = load_experiment_config(repo_root / "configs/experiments/smoke-synthetic.yaml")
    a = run_smoke(config, tmp_path / "a")
    b = run_smoke(config, tmp_path / "b")
    assert a["metrics"] == b["metrics"]


def test_unimplemented_models_fail_loudly() -> None:
    with pytest.raises(NotImplementedError, match="M2"):
        build_estimator(ModelConfig(name="lightgbm"), seed=0)


def test_seed_must_not_be_set_in_model_params() -> None:
    with pytest.raises(ValueError, match="seed"):
        build_estimator(ModelConfig(name="decision_tree", params={"random_state": 1}), seed=0)
