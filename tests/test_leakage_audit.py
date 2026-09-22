"""Duplicate and target-leakage audit for a train/test split (M2)."""

from __future__ import annotations

import pandas as pd
import pytest

from driftguard.preprocessing.leakage_audit import audit_leakage


@pytest.fixture
def clean_split() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.DataFrame(
        {
            "f1": range(100),
            "f2": [i % 7 for i in range(100)],
            "label": ["a" if i % 2 == 0 else "b" for i in range(100)],
        }
    )
    test = pd.DataFrame(
        {
            "f1": range(1000, 1050),
            "f2": [i % 7 for i in range(50)],
            "label": ["a" if i % 2 == 0 else "b" for i in range(50)],
        }
    )
    return train, test


def test_no_cross_partition_duplicates_when_partitions_are_disjoint(
    clean_split: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    train, test = clean_split
    report = audit_leakage(train, test, ["f1", "f2"], "label")
    assert report.cross_partition_duplicate_rows == 0
    assert report.exact_duplicate_rows_train == 0
    assert report.exact_duplicate_rows_test == 0


def test_detects_a_row_leaked_into_both_partitions(
    clean_split: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    train, test = clean_split
    leaked = pd.concat([test, train.iloc[[3]]], ignore_index=True)
    report = audit_leakage(train, leaked, ["f1", "f2"], "label")
    assert report.cross_partition_duplicate_rows == 1


def test_detects_within_partition_exact_duplicates() -> None:
    train = pd.DataFrame({"f1": [1, 1, 2, 3], "label": ["a", "a", "b", "b"]})
    test = pd.DataFrame({"f1": [9], "label": ["a"]})
    report = audit_leakage(train, test, ["f1"], "label")
    assert report.exact_duplicate_rows_train == 1


def test_flags_a_column_that_deterministically_encodes_the_label() -> None:
    # `leaky` is a 1:1 recoding of `label` - a textbook target-leakage column.
    n = 200
    train = pd.DataFrame(
        {
            "leaky": [f"code-{i % 2}" for i in range(n)],
            "noise": range(n),
            "label": ["a" if i % 2 == 0 else "b" for i in range(n)],
        }
    )
    test = pd.DataFrame({"leaky": ["code-0"], "noise": [0], "label": ["a"]})
    report = audit_leakage(train, test, ["leaky", "noise"], "label")
    assert "leaky" in report.high_purity_columns
    assert report.high_purity_columns["leaky"] == pytest.approx(1.0)
    assert "leaky" in report.excluded_columns
    assert "noise" not in report.excluded_columns
    assert "label purity" in report.exclusion_reasons["leaky"]


def test_identifier_columns_are_always_excluded_regardless_of_purity(
    clean_split: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    train, test = clean_split
    report = audit_leakage(train, test, ["f1", "f2"], "label", identifier_columns=["f1"])
    assert "f1" in report.excluded_columns
    assert "identifier column" in report.exclusion_reasons["f1"]


def test_purity_decision_uses_train_partition_only() -> None:
    """A column that is leaky ONLY in test must not be excluded - the decision is
    computed from train, so it must be blind to a leak that exists only in test."""
    n = 200
    train = pd.DataFrame(
        {
            "col": [i % 5 for i in range(n)],  # not label-pure on train
            "label": ["a" if i % 2 == 0 else "b" for i in range(n)],
        }
    )
    test = pd.DataFrame({"col": ["only-in-test"] * 10, "label": ["a"] * 10})
    report = audit_leakage(train, test, ["col"], "label")
    assert "col" not in report.high_purity_columns
    assert "col" not in report.excluded_columns


def test_high_cardinality_id_like_columns_are_not_flagged_by_purity_alone() -> None:
    # A near-unique row id is "pure" by construction but excluded from purity scoring
    # via the cardinality guard (>50% of rows), so it must be excluded explicitly via
    # identifier_columns rather than silently caught here.
    n = 200
    train = pd.DataFrame(
        {
            "row_id": [f"id-{i}" for i in range(n)],
            "label": ["a" if i % 2 == 0 else "b" for i in range(n)],
        }
    )
    test = pd.DataFrame({"row_id": ["id-9999"], "label": ["a"]})
    report = audit_leakage(train, test, ["row_id"], "label")
    assert "row_id" not in report.high_purity_columns
