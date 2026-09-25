"""`driftguard stream` commands that do not need a long-running broker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from driftguard.cli import app
from driftguard.streaming.broker import find_mosquitto_tool

REPO = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_demo_bundle_is_synthetic_and_not_publishable(tmp_path: Path) -> None:
    out = tmp_path / "bundle"
    config = REPO / "configs/experiments/stream-demo-synthetic.yaml"
    result = runner.invoke(
        app, ["stream", "demo-bundle", "--out-dir", str(out), "--config", str(config)]
    )
    assert result.exit_code == 0, result.output
    meta = json.loads((out / "bundle.json").read_text())
    assert meta["synthetic_data"] is True and meta["publication_allowed"] is False
    assert "NON-REPORTABLE" in result.output


def test_demo_bundle_refuses_registry_configs(tmp_path: Path) -> None:
    config = REPO / "configs/experiments/m3-edge_iiotset-dt-lgbm-seed42.yaml"
    result = runner.invoke(
        app, ["stream", "demo-bundle", "--out-dir", str(tmp_path / "b"), "--config", str(config)]
    )
    assert result.exit_code != 0


def test_broker_config_rejects_partial_tls_and_public_plaintext(tmp_path: Path) -> None:
    partial = runner.invoke(
        app,
        [
            "stream",
            "broker-config",
            "--out-dir",
            str(tmp_path / "a"),
            "--tls-ca",
            str(REPO / "README.md"),
        ],
    )
    assert partial.exit_code != 0
    try:
        find_mosquitto_tool("mosquitto_passwd")
    except FileNotFoundError:
        pytest.skip("mosquitto_passwd not installed")
    public = runner.invoke(
        app,
        ["stream", "broker-config", "--out-dir", str(tmp_path / "b"), "--bind", "0.0.0.0"],  # noqa: S104
    )
    assert public.exit_code == 2 and "TLS" in public.output
    ok = runner.invoke(app, ["stream", "broker-config", "--out-dir", str(tmp_path / "c")])
    assert ok.exit_code == 0
    assert "PASSWORD" not in ok.output  # secrets are written to disk, never printed


def test_replay_requires_run_dir_for_heldout(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["stream", "replay", "--bundle", str(tmp_path), "--source", "heldout"]
    )
    assert result.exit_code != 0
