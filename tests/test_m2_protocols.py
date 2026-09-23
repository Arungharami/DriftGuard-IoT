"""M2: synthetic tests proving the leakage-safe protocol never fits on test data, and that
the paper-faithful protocol's leakage is detected and flagged (never reportable)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.feature_selection import mutual_info_classif
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import PreprocessingConfig, ResamplingConfig
from driftguard.data.synthetic import LABEL_COLUMN, NUMERIC_FEATURES
from driftguard.preprocessing.paper_protocol import PaperDatasetProtocol
from driftguard.preprocessing.protocols import (
    build_leakage_safe_pipeline,
    prepare_leakage_safe,
    prepare_paper_faithful,
)
from driftguard.preprocessing.transformers import (
    MutualInformationSelector,
    NumericCoercer,
    canonical_category,
    proportional_resample,
    proportional_targets,
)

NUMERIC = list(NUMERIC_FEATURES)
CATEGORICAL = ["proto"]


def _cfg(**kw: Any) -> PreprocessingConfig:
    return PreprocessingConfig(**{"mi_threshold": 0.0, "mi_max_samples": None, **kw})


@pytest.fixture
def prepared(synthetic_flows: pd.DataFrame):  # type: ignore[no-untyped-def]
    return prepare_leakage_safe(
        synthetic_flows,
        target=LABEL_COLUMN,
        numeric_columns=NUMERIC,
        categorical_columns=CATEGORICAL,
        test_size=0.3,
        seed=1,
        deduplicate=True,
    )


def _pipe(cfg: PreprocessingConfig | None = None):  # type: ignore[no-untyped-def]
    return build_leakage_safe_pipeline(
        NUMERIC, CATEGORICAL, DecisionTreeClassifier(random_state=0), cfg or _cfg(), seed=0
    )


# --------------------------------------------------------------------------- leakage-safe


def test_partitions_are_disjoint_and_complete(prepared, synthetic_flows) -> None:  # type: ignore[no-untyped-def]
    assert prepared.X_train.index.intersection(prepared.X_test.index).empty
    assert len(prepared.X_train) + len(prepared.X_test) == len(synthetic_flows)
    assert prepared.details["test_contains_synthetic_rows"] is False


def test_every_fitted_step_receives_only_training_rows(prepared) -> None:  # type: ignore[no-untyped-def]
    seen: list[pd.Index] = []
    real_fit = NumericCoercer.fit

    def spy(self: NumericCoercer, X: pd.DataFrame, y: Any = None) -> NumericCoercer:
        seen.append(X.index)
        return real_fit(self, X, y)

    with patch.object(NumericCoercer, "fit", spy):
        pipe = _pipe(_cfg(resampling=ResamplingConfig(strategy="paper_proportional", ratio=1.5)))
        pipe.fit(prepared.X_train, prepared.y_train)
        pipe.predict(prepared.X_test)
    assert seen, "pipeline entry step was never fitted"
    for index in seen:
        assert index.isin(prepared.X_train.index).all()
        assert not index.isin(prepared.X_test.index).any()


def test_mutual_information_scorer_never_receives_test_rows(prepared) -> None:  # type: ignore[no-untyped-def]
    counts: list[int] = []

    def spy(x: Any, y: Any, **kw: Any) -> Any:
        counts.append(len(x))
        return mutual_info_classif(x, y, **kw)

    with patch("driftguard.preprocessing.transformers.mutual_info_classif", spy):
        pipe = _pipe()
        pipe.fit(prepared.X_train, prepared.y_train)
        pipe.predict(prepared.X_test)
    assert counts == [len(prepared.X_train)]


def test_signal_present_only_in_test_rows_is_not_selected(prepared) -> None:  # type: ignore[no-untyped-def]
    """A feature that perfectly encodes the label on test rows (noise on train rows) must not
    be selected when MI is fitted on train only; fitting on all rows would select it."""
    rng = np.random.default_rng(0)
    codes = {c: i for i, c in enumerate(sorted(prepared.y_train.unique()))}
    x_train = prepared.X_train.assign(leak=rng.normal(size=len(prepared.X_train)))
    x_test = prepared.X_test.assign(leak=prepared.y_test.map(codes).astype(float) * 10.0)

    selector = MutualInformationSelector(threshold=0.05, random_state=0)
    train_only = selector.fit(x_train[["leak", *NUMERIC]], prepared.y_train)
    assert "leak" not in train_only.selected_features_

    everything = MutualInformationSelector(threshold=0.05, random_state=0).fit(
        pd.concat([x_train, x_test])[["leak", *NUMERIC]],
        pd.concat([prepared.y_train, prepared.y_test]),
    )
    assert "leak" in everything.selected_features_


def test_encoder_and_imputer_learn_from_train_only(prepared) -> None:  # type: ignore[no-untyped-def]
    x_train = prepared.X_train.copy()
    x_train.iloc[0, x_train.columns.get_loc("duration")] = np.nan
    pipe = _pipe()
    pipe.fit(x_train, prepared.y_train)

    encode = pipe.named_steps["encode"]
    imputer = encode.named_transformers_["num"]
    expected_median = x_train["duration"].median()
    assert imputer.statistics_[NUMERIC.index("duration")] == pytest.approx(expected_median)

    x_test = prepared.X_test.copy()
    x_test["proto"] = "never-seen-in-train"
    categories = encode.named_transformers_["cat"].categories_[0]
    assert "never-seen-in-train" not in set(categories)
    assert len(pipe.predict(x_test)) == len(x_test)


def test_resampling_happens_at_fit_only_and_uses_train_counts(prepared) -> None:  # type: ignore[no-untyped-def]
    pipe = _pipe(_cfg(resampling=ResamplingConfig(strategy="paper_proportional", ratio=2.0)))
    pipe.fit(prepared.X_train, prepared.y_train)
    rs = pipe.named_steps["resample"]
    assert rs.n_input_rows_ == len(prepared.X_train)
    assert rs.n_synthetic_rows_ > 0
    targets = proportional_targets(
        prepared.y_train.value_counts(), round(2.0 * len(prepared.X_train))
    )
    assert rs.n_output_rows_ == sum(targets.values())
    assert len(pipe.predict(prepared.X_test)) == len(prepared.X_test)


def test_deduplication_prevents_identical_rows_across_split(synthetic_flows: pd.DataFrame) -> None:
    dup = pd.concat([synthetic_flows, synthetic_flows.iloc[:300]], ignore_index=True)
    out = prepare_leakage_safe(
        dup,
        target=LABEL_COLUMN,
        numeric_columns=NUMERIC,
        categorical_columns=CATEGORICAL,
        test_size=0.3,
        seed=3,
        deduplicate=True,
    )
    assert out.details["duplicates_removed"] == 300
    train = pd.concat([out.X_train, out.y_train], axis=1)
    test = pd.concat([out.X_test, out.y_test], axis=1)
    assert train.merge(test, how="inner").empty


# --------------------------------------------------------------------------- paper-faithful


def _paper_protocol() -> PaperDatasetProtocol:
    return PaperDatasetProtocol(
        dataset_id="synthetic",
        target_column=LABEL_COLUMN,
        original_rows=0,
        model_ready_rows=0,
        pre_mi_drop=("timestamp",),
        reported_mi_removed=(),
        figure_mi_features=(),
        figure="n/a",
    )


def test_paper_faithful_leakage_is_measured_and_flagged(synthetic_flows: pd.DataFrame) -> None:
    cfg = PreprocessingConfig(
        protocol="paper_faithful",
        deduplicate=False,
        mi_max_samples=None,
        resampling=ResamplingConfig(strategy="paper_proportional", ratio=2.0, random_state=42),
    )
    out = prepare_paper_faithful(
        synthetic_flows, protocol=_paper_protocol(), cfg=cfg, test_size=0.3, seed=1
    )
    d = out.details
    assert d["rows_after_resampling"] > len(synthetic_flows)
    assert d["test_contains_synthetic_rows"] is True
    assert d["synthetic_rows_in_test"] > 0
    assert "FULL dataset" in d["fit_scope"]
    assert any("before the train/test split" in r for r in d["leakage_risks"])
    assert "proto" not in d["mi_universe"]  # paper MI universe is numeric columns only


def test_paper_faithful_config_refuses_deduplication() -> None:
    with pytest.raises(ValueError, match="does not deduplicate"):
        PreprocessingConfig(protocol="paper_faithful", deduplicate=True)


# --------------------------------------------------------------------------- resampling


def test_proportional_resample_preserves_class_proportions() -> None:
    y = pd.Series(["a"] * 700 + ["b"] * 250 + ["c"] * 50)
    X = pd.DataFrame({"f": np.arange(1000, dtype=float), "g": np.arange(1000, dtype=float) % 7})
    X_res, y_res, synthetic = proportional_resample(X, y, total=2000, random_state=0)
    counts = y_res.value_counts()
    assert dict(counts) == proportional_targets(y.value_counts(), 2000)
    assert counts["a"] / len(y_res) == pytest.approx(0.70, abs=1e-3)
    assert int(synthetic.sum()) == len(y_res) - 1000
    assert len(X_res) == len(y_res)


def test_proportional_resample_downsamples_without_synthetic_rows() -> None:
    y = pd.Series(["a"] * 900 + ["b"] * 100)
    X = pd.DataFrame({"f": np.arange(1000, dtype=float)})
    _, y_res, synthetic = proportional_resample(X, y, total=500, random_state=0)
    assert dict(y_res.value_counts()) == {"a": 450, "b": 50}
    assert not synthetic.any()


def test_classes_too_small_for_smote_are_left_unchanged() -> None:
    y = pd.Series(["a"] * 99 + ["b"])
    X = pd.DataFrame({"f": np.arange(100, dtype=float)})
    _, y_res, _ = proportional_resample(X, y, total=300, random_state=0)
    assert (y_res == "b").sum() == 1


# --------------------------------------------------------------------------- canonicalisation


@pytest.mark.parametrize(
    ("a", "b"), [("0", "0.0"), ("0", "0x00000000"), ("1", "1.0"), (None, float("nan")), ("-", "")]
)
def test_numerically_equal_spellings_collapse(a: object, b: object) -> None:
    assert canonical_category(a) == canonical_category(b)


def test_non_numeric_categories_are_kept() -> None:
    assert canonical_category("MQTT") == "MQTT"
    assert canonical_category("MQTT") != canonical_category("0")
