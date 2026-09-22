from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from driftguard.evaluation.metrics import classification_metrics
from driftguard.reporting.provenance import sha256_file


def test_sha256_file_matches_hashlib(tmp_path: Path) -> None:
    data = b"driftguard" * 500_000  # > 1 chunk
    path = tmp_path / "blob.bin"
    path.write_bytes(data)
    assert sha256_file(path, chunk_size=4096) == hashlib.sha256(data).hexdigest()


def test_metrics_on_known_predictions() -> None:
    y_true = ["a", "a", "b", "b", "c", "c"]
    y_pred = ["a", "a", "b", "a", "c", "b"]
    m = classification_metrics(y_true, y_pred, labels=["a", "b", "c"])
    assert m["recall_per_class"] == {"a": 1.0, "b": 0.5, "c": 0.5}
    assert m["balanced_accuracy"] == pytest.approx(2 / 3)
    assert m["micro_f1"] == pytest.approx(4 / 6)
    # per-class F1: a=0.8, b=0.5, c=2/3
    assert m["macro_f1"] == pytest.approx((0.8 + 0.5 + 2 / 3) / 3)
    assert m["n_samples"] == 6


def test_perfect_predictions() -> None:
    y = ["x", "y", "x", "y"]
    m = classification_metrics(y, y, labels=["x", "y"])
    assert m["macro_f1"] == 1.0
    assert m["mcc"] == 1.0
