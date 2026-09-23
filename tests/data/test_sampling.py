from __future__ import annotations

import pandas as pd
import pytest

from driftguard.data.sampling import SubsetSpec, deterministic_sample


@pytest.fixture
def imbalanced() -> pd.DataFrame:
    labels = ["normal"] * 900 + ["dos"] * 90 + ["rare"] * 10
    return pd.DataFrame({"t": range(1000), "label": labels}).sample(frac=1, random_state=0)


def spec(
    n: int, seed: int = 1, stratify: str | None = "label", min_per_class: int = 1
) -> SubsetSpec:
    return SubsetSpec(n=n, seed=seed, stratify_column=stratify, min_per_class=min_per_class)


def test_same_spec_same_rows(imbalanced: pd.DataFrame) -> None:
    a = deterministic_sample(imbalanced, spec(100))
    b = deterministic_sample(imbalanced, spec(100))
    c = deterministic_sample(imbalanced, spec(100, seed=2))
    pd.testing.assert_frame_equal(a, b)
    assert not a.index.equals(c.index)


def test_preserves_source_order(imbalanced: pd.DataFrame) -> None:
    ordered = imbalanced.sort_values("t")
    out = deterministic_sample(ordered, spec(100))
    assert out["t"].is_monotonic_increasing


def test_stratified_allocation_is_proportional_with_minimum(imbalanced: pd.DataFrame) -> None:
    out = deterministic_sample(imbalanced, spec(100, min_per_class=5))
    counts = out["label"].value_counts()
    assert len(out) == 100
    assert counts["rare"] >= 5
    assert counts["normal"] > counts["dos"] > 0


def test_min_per_class_capped_by_class_size(imbalanced: pd.DataFrame) -> None:
    out = deterministic_sample(imbalanced, spec(200, min_per_class=50))
    assert out["label"].value_counts()["rare"] == 10


def test_unstratified_and_oversized(imbalanced: pd.DataFrame) -> None:
    assert len(deterministic_sample(imbalanced, spec(37, stratify=None))) == 37
    assert len(deterministic_sample(imbalanced, spec(5000))) == len(imbalanced)


def test_errors(imbalanced: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="minimum"):
        deterministic_sample(imbalanced, spec(10, min_per_class=5))
    with pytest.raises(ValueError, match="positive"):
        deterministic_sample(imbalanced, spec(0))
    bad = imbalanced.copy()
    bad.loc[bad.index[0], "label"] = None
    with pytest.raises(ValueError, match="missing"):
        deterministic_sample(bad, spec(50))


def test_subset_id_depends_on_source_and_parameters() -> None:
    s = spec(100)
    assert s.subset_id("a" * 64) == spec(100).subset_id("a" * 64)
    assert s.subset_id("a" * 64) != s.subset_id("b" * 64)
    assert s.subset_id("a" * 64) != spec(101).subset_id("a" * 64)
