from __future__ import annotations

import pytest

from driftguard.data.fixtures import synthesize_table
from driftguard.data.registry import TableSpec
from driftguard.data.schema import validate_frame, validate_header
from tests.data.conftest import ALL_TABLES


@pytest.mark.parametrize(("dataset_id", "table"), ALL_TABLES)
def test_schema_fixture_validates_for_every_table(dataset_id: str, table: TableSpec) -> None:
    df = synthesize_table(table, n=200, seed=0)
    report = validate_frame(df, table)
    assert report.ok, report.errors
    assert report.type_violations == {}
    assert list(df.columns) == table.required_columns
    assert set(df[table.label_column]) == {0, 1}


def test_fixture_is_deterministic(ton_table: TableSpec) -> None:
    a = synthesize_table(ton_table, n=50, seed=3)
    b = synthesize_table(ton_table, n=50, seed=3)
    assert a.equals(b)


def test_optional_columns_may_be_present_or_absent(ton_table: TableSpec) -> None:
    with_opt = synthesize_table(ton_table, n=20, seed=0, include_optional=True)
    assert "http_referrer" in with_opt.columns
    assert validate_frame(with_opt, ton_table).ok


def test_missing_and_unexpected_columns_are_errors(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=20, seed=0).drop(columns=["duration"])
    df["surprise"] = 1
    report = validate_frame(df, ton_table)
    assert not report.ok
    assert report.missing_columns == ["duration"]
    assert report.unexpected_columns == ["surprise"]


def test_type_violations_are_warnings(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=20, seed=0)
    df["duration"] = df["duration"].astype(object)
    df.loc[0, "duration"] = "not-a-number"
    df["src_bytes"] = df["src_bytes"].astype(float)
    df.loc[1, "src_bytes"] = 1.5
    report = validate_frame(df, ton_table)
    assert report.ok
    assert report.type_violations == {"duration": 1, "src_bytes": 1}


def test_declared_na_values_are_not_type_violations(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=20, seed=0)
    df["duration"] = df["duration"].astype(object)
    df.loc[0, "duration"] = "-"  # TON_IoT's documented missing-value marker
    assert "duration" not in validate_frame(df, ton_table).type_violations


def test_header_only_validation_and_order(ton_table: TableSpec) -> None:
    header = list(reversed(ton_table.required_columns))
    report = validate_header(header, ton_table)
    assert report.ok
    assert not report.order_matches
    assert any("provisional" in w for w in report.warnings)
