from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import ks_2samp

from driftguard.data.synthetic import (
    CATEGORICAL_FEATURES,
    LABEL_COLUMN,
    NUMERIC_FEATURES,
    SYNTHETIC_ATTR,
    TIMESTAMP_COLUMN,
    generate_synthetic_flows,
)


def test_schema(synthetic_flows: pd.DataFrame) -> None:
    expected = [TIMESTAMP_COLUMN, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES, LABEL_COLUMN]
    assert list(synthetic_flows.columns) == expected
    assert synthetic_flows.attrs[SYNTHETIC_ATTR] is True
    assert (synthetic_flows[list(NUMERIC_FEATURES)] > 0).all().all()
    assert synthetic_flows[TIMESTAMP_COLUMN].is_monotonic_increasing


def test_deterministic_for_seed() -> None:
    a = generate_synthetic_flows(n_samples=300, seed=11)
    b = generate_synthetic_flows(n_samples=300, seed=11)
    c = generate_synthetic_flows(n_samples=300, seed=12)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_class_imbalance_follows_proportions(synthetic_flows: pd.DataFrame) -> None:
    freq = synthetic_flows[LABEL_COLUMN].value_counts(normalize=True)
    assert freq.idxmax() == "normal"
    assert freq["injection"] < freq["dos"]
    assert set(freq.index) == {"normal", "dos", "scan", "injection"}


def test_every_class_present_even_when_rare() -> None:
    df = generate_synthetic_flows(
        n_samples=60, seed=0, class_proportions={"normal": 0.98, "rare": 0.02}
    )
    assert (df[LABEL_COLUMN] == "rare").sum() >= 1


def test_drift_shifts_only_selected_features_after_onset(drifted_flows: pd.DataFrame) -> None:
    clean = generate_synthetic_flows(n_samples=2000, seed=7)
    onset = 1000
    # Before onset the drifted and clean tables are identical.
    pd.testing.assert_frame_equal(drifted_flows.iloc[:onset], clean.iloc[:onset])
    # After onset only src_bytes is scaled.
    np.testing.assert_allclose(
        drifted_flows["src_bytes"].iloc[onset:], clean["src_bytes"].iloc[onset:] * 4.0
    )
    pd.testing.assert_series_equal(drifted_flows["dst_bytes"], clean["dst_bytes"])
    # The shift is statistically visible.
    pre, post = drifted_flows["src_bytes"].iloc[:onset], drifted_flows["src_bytes"].iloc[onset:]
    assert ks_2samp(pre, post).pvalue < 1e-6


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n_samples": 2}, "at least the number of classes"),
        ({"drift_features": ("proto",), "drift_onset_fraction": 0.5}, "numeric features"),
        ({"drift_onset_fraction": 1.5, "drift_features": ("src_bytes",)}, r"\(0, 1\)"),
    ],
)
def test_invalid_arguments(kwargs: dict[str, object], message: str) -> None:
    params: dict[str, object] = {"n_samples": 200, "seed": 0, **kwargs}
    with pytest.raises(ValueError, match=message):
        generate_synthetic_flows(**params)  # type: ignore[arg-type]
