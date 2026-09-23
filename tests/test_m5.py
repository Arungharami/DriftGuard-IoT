"""Adversarial checks of M5 isolation and statistical mechanics, synthetic only."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.tree import DecisionTreeClassifier
from typer.testing import CliRunner

from driftguard.cli import app
from driftguard.m5.evaluation import (
    assert_isolated,
    assert_unknown_withheld,
    benchmark_predict,
    defensive_corruption,
    delayed_prequential,
    frozen_transfer,
    paired_block_interval,
    shap_stability,
    unknown_metrics,
    unknown_threshold,
)
from driftguard.m5.readiness import inventory
from driftguard.m5.smoke import run_smoke


class LastLabel(ClassifierMixin, BaseEstimator):
    def fit(self, x, y):
        self.label = y[-1]
        return self

    def predict(self, x):
        return np.repeat(self.label, len(x))


def stream(**kwargs):
    options = dict(
        estimator=LastLabel(),
        initial_x=np.array([[0], [1]]),
        initial_y=np.array([0, 0]),
        stream_x=np.arange(2, 7).reshape(-1, 1),
        stream_y=np.array([1, 0, 1, 0, 1]),
        initial_time=np.array([0, 1]),
        event_time=np.array([2, 3, 3, 4, 5]),
        label_time=np.array([3, 3, 4, 5, 6]),
        policy="periodic",
        period=1,
    )
    options.update(kwargs)
    return delayed_prequential(**options)


def test_delayed_labels_and_timestamp_ties():
    result = stream()
    assert result["predictions"].tolist() == [0, 0, 0, 0, 1]
    assert result["updates"] == [
        {"at": 4.0, "released_indices": [0, 1]},
        {"at": 5.0, "released_indices": [0, 1, 2]},
    ]
    assert result["unreleased_at_end"] == 2


def test_future_label_poisoning_cannot_change_past_predictions():
    baseline = stream()
    changed = stream(stream_y=np.array([1, 0, 1, 999, 999]))
    np.testing.assert_array_equal(baseline["predictions"], changed["predictions"])


def test_frozen_never_adapts_and_triggered_uses_released_errors():
    assert stream(policy="frozen")["updates"] == []
    result = stream(policy="error_triggered", error_window=1, error_threshold=0.5)
    assert all(u["at"] > 3 for u in result["updates"])


@pytest.mark.parametrize(
    "changes",
    [
        {"event_time": np.array([3, 2, 3, 4, 5])},
        {"initial_time": np.array([0, 2])},
        {"label_time": np.array([1, 3, 4, 5, 6])},
        {"policy": "invalid"},
        {"period": 0},
        {"error_threshold": 2},
        {"stream_y": np.array([1])},
    ],
)
def test_invalid_stream_rejected(changes):
    with pytest.raises(ValueError):
        stream(**changes)


def test_cross_partition_duplicate_features_rejected():
    with pytest.raises(ValueError, match="feature-identical"):
        assert_isolated(np.array([[0, 1]]), np.array([[0, 1]]))
    with pytest.raises(ValueError):
        assert_isolated(np.array([[np.nan]]))


def test_paired_identical_predictions_have_exact_zero_interval():
    y = np.tile([0, 1], 10)
    result = paired_block_interval(y, y, y, classes=[0, 1], block_size=2, repeats=100)
    assert result["estimate"] == result["low"] == result["high"] == 0
    assert result["includes_training_uncertainty"] is False


def test_paired_negative_result_preserved_and_reproducible():
    y = np.tile([0, 1], 10)
    a = paired_block_interval(y, y, 1 - y, classes=[0, 1], block_size=2, repeats=100)
    b = paired_block_interval(y, y, 1 - y, classes=[0, 1], block_size=2, repeats=100)
    assert a == b
    assert a["estimate"] == a["low"] == a["high"] == -1


@pytest.mark.parametrize("block,repeats", [(0, 100), (20, 100), (1, 99)])
def test_invalid_bootstrap_configuration(block, repeats):
    y = np.tile([0, 1], 10)
    with pytest.raises(ValueError):
        paired_block_interval(y, y, y, classes=[0, 1], block_size=block, repeats=repeats)


def test_unknown_threshold_and_ties():
    threshold = unknown_threshold(np.array([0, 0, 0, 1]), false_reject_rate=0.25)
    assert threshold == 1
    result = unknown_metrics(np.array([0, 1, 2, 3]), np.array([0, 0, 1, 1]), threshold=threshold)
    assert result["known_false_reject_rate"] == 0
    assert result["unknown_recall"] == result["auroc"] == 1
    with pytest.raises(ValueError):
        unknown_metrics(np.array([1, 2]), np.array([0, 0]), threshold=1)
    with pytest.raises(ValueError, match="leaked"):
        assert_unknown_withheld(["normal"], ["unknown"], held_out="unknown")


def test_corruption_is_bounded_aggregate_only_and_does_not_mutate():
    x = np.arange(24, dtype=float).reshape(12, 2)
    original = x.copy()
    calls = []

    def predict(values):
        calls.append(values.copy())
        return np.zeros(len(values))

    result = defensive_corruption(predict, x, np.zeros(12), x, mutable_columns=[0], fraction=0.05)
    np.testing.assert_array_equal(x, original)
    np.testing.assert_array_equal(calls[0][:, 1], calls[1][:, 1])
    iqr = np.subtract(*np.percentile(x[:, 0], [75, 25]))
    assert np.max(np.abs(calls[1][:, 0] - calls[0][:, 0])) <= 0.05 * iqr
    assert all(np.isscalar(value) for value in result.values())
    with pytest.raises(ValueError, match="budget"):
        defensive_corruption(predict, x, np.zeros(12), x, mutable_columns=[0], fraction=0.1)


def test_shap_ties_and_undefined_values():
    values = np.array([[2.0, 2.0, 0.0]])
    result = shap_stability(values, values[:, ::-1], feature_names=["a", "b", "c"], top_k=1)
    assert result["jaccard"] == 1 / 3
    assert (
        shap_stability(values * 0, values, feature_names=["a", "b", "c"], top_k=1)["status"]
        == "undefined"
    )


def test_frozen_transfer_clones_estimator_and_has_no_target_labels():
    model = DecisionTreeClassifier(random_state=0)
    prediction = frozen_transfer(
        model, np.array([[0], [1]]), np.array([0, 1]), np.array([[2], [3]])
    )
    assert prediction.tolist() == [1, 1]
    assert not hasattr(model, "tree_")


def test_benchmark_units_and_nonnegative_measurements():
    result = benchmark_predict(lambda x: np.zeros(len(x)), np.ones((2, 1)), repeats=10)
    assert result["p99"] >= result["p95"] >= result["p50"] >= 0
    assert result["latency_unit"] == "seconds_per_batch"
    assert result["peak_rss"] is None


def test_audit_blocks_missing_files_and_unlicensed_data(tmp_path: Path):
    result = inventory(tmp_path)
    assert result["reportable"] is False
    assert result["campaign_status"] == "blocked"
    assert all(not row["inventory_passed"] for row in result["datasets"])
    wustl = next(d for d in result["datasets"] if d["dataset"] == "wustl_iiot_2021")
    assert any("permission" in reason for reason in wustl["blockers"])
    assert CliRunner().invoke(app, ["m5-audit", "--root", str(tmp_path)]).exit_code == 2


def test_smoke_never_claims_research(tmp_path: Path):
    result = run_smoke(tmp_path)
    assert result["kind"] == "smoke" and result["synthetic_data"]
    assert not result["reportable"]
    assert result["frozen_transfer_matches_stream"]
    assert len(result["data_sha256"]) == 64
    assert (tmp_path / "m5-smoke.json").is_file()
