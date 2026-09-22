from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/check_repo_hygiene.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_repo_hygiene", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hygiene = _load()


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "apps/research-portal/.env.production",
        "kaggle.json",
        "data/raw/TON_IoT.zip",
        "data/raw/edge.tar.gz",
        "traces/capture.pcap",
        "data/processed/train.parquet",
        "data/raw/wustl.csv",
        "artifacts/model.joblib",
        "artifacts/model.pkl",
        "artifacts/model.safetensors",
        "certs/server.pem",
    ],
)
def test_blocked_paths(path: str) -> None:
    assert hygiene.classify(path) is not None


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        "tests/fixtures/tiny_flows.csv",
        "configs/experiments/smoke-synthetic.yaml",
        "src/driftguard/cli.py",
        "apps/research-portal/public/results/index.json",
    ],
)
def test_allowed_paths(path: str) -> None:
    assert hygiene.classify(path) is None


def test_large_files_are_blocked() -> None:
    assert hygiene.classify("docs/figure.png", size_bytes=hygiene.MAX_FILE_BYTES + 1) is not None
    assert hygiene.classify("docs/figure.png", size_bytes=1024) is None


def test_find_violations_reads_sizes(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_bytes(b"0" * (hygiene.MAX_FILE_BYTES + 1))
    (tmp_path / "ok.txt").write_text("fine", encoding="utf-8")
    found = hygiene.find_violations(["big.txt", "ok.txt"], tmp_path)
    assert [v.path for v in found] == ["big.txt"]


def test_current_repository_is_clean() -> None:
    root = SCRIPT.parent.parent
    violations = hygiene.find_violations(hygiene.tracked_files(root), root)
    assert violations == [], violations
