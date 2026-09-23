"""Shared fixtures: one SYNTHETIC demo bundle per session (never research evidence)."""

from __future__ import annotations

from pathlib import Path

import pytest

from driftguard.config import load_experiment_config
from driftguard.experiments import run_experiment
from driftguard.platform.bundle import LoadedBundle, load_bundle, prepare_bundle

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def bundle_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    config = load_experiment_config(REPO / "configs/experiments/stream-demo-synthetic.yaml")
    root = tmp_path_factory.mktemp("stream")
    result = run_experiment(config, root / "runs")
    prepare_bundle(Path(result["run_dir"]), "decision_tree", root / "bundle")
    return root / "bundle"


@pytest.fixture(scope="session")
def bundle(bundle_dir: Path) -> LoadedBundle:
    return load_bundle(bundle_dir)
