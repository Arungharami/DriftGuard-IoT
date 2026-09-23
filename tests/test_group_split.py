"""Feature-group split: conflicting-label duplicates never straddle train/test, and the
split is recorded so it can be re-derived (synthetic data only)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from driftguard.data.synthetic import LABEL_COLUMN, NUMERIC_FEATURES
from driftguard.experiments import _index_sha256, run_experiment
from driftguard.preprocessing.protocols import prepare_leakage_safe
from tests.test_m2_experiments import _synthetic_config

NUMERIC = list(NUMERIC_FEATURES)
CATEGORICAL = ["proto"]


def _with_conflicts(flows: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    """Append feature-identical copies of ``n`` rows carrying a different label."""
    labels = sorted(flows[LABEL_COLUMN].unique())
    copies = flows.iloc[:n].copy()
    copies[LABEL_COLUMN] = [
        labels[(labels.index(v) + 1) % len(labels)] for v in copies[LABEL_COLUMN]
    ]
    return pd.concat([flows, copies], ignore_index=True)


def _prepare(df: pd.DataFrame, seed: int = 5):  # type: ignore[no-untyped-def]
    return prepare_leakage_safe(
        df,
        target=LABEL_COLUMN,
        numeric_columns=NUMERIC,
        categorical_columns=CATEGORICAL,
        test_size=0.3,
        seed=seed,
        deduplicate=True,
    )


def test_conflicting_label_groups_stay_in_one_partition(synthetic_flows: pd.DataFrame) -> None:
    out = _prepare(_with_conflicts(synthetic_flows))
    assert out.details["conflicting_label_groups"] == 200
    assert out.details["conflicting_label_rows"] == 400
    assert out.details["cross_split_feature_duplicates"] == 0
    features = NUMERIC + CATEGORICAL
    assert out.X_train[features].merge(out.X_test[features], how="inner").empty
    assert abs(len(out.X_test) / (len(out.X_train) + len(out.X_test)) - 0.3) < 0.02


def test_group_split_is_deterministic_and_seed_sensitive(synthetic_flows: pd.DataFrame) -> None:
    df = _with_conflicts(synthetic_flows)
    a, b, c = _prepare(df, 5), _prepare(df, 5), _prepare(df, 6)
    assert _index_sha256(a.X_test.index) == _index_sha256(b.X_test.index)
    assert _index_sha256(a.X_test.index) != _index_sha256(c.X_test.index)


def test_every_class_present_in_both_partitions(synthetic_flows: pd.DataFrame) -> None:
    out = _prepare(synthetic_flows)
    assert out.details["stratified"] is True
    assert set(out.y_train) == set(out.y_test) == set(synthetic_flows[LABEL_COLUMN])


def test_run_writes_verifiable_split_record(tmp_path: Path) -> None:
    result = run_experiment(_synthetic_config(), tmp_path, save_models=False)
    run_dir = Path(result["run_dir"])
    record = result["manifest"].protocol_details["split_record"]
    stored = json.loads((run_dir / record["file"]).read_text(encoding="utf-8"))
    assert set(stored["train_index"]).isdisjoint(stored["test_index"])
    assert len(stored["test_index"]) == result["n_test"]
    assert sum(record["class_counts"]["test"].values()) == result["n_test"]
    assert record["test_index_sha256"] == _index_sha256(pd.Index(stored["test_index"]))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["protocol_details"]["split_record"]["file_sha256"] == record["file_sha256"]
