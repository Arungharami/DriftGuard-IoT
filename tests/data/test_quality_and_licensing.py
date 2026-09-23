from __future__ import annotations

import pandas as pd
import pytest

from driftguard.data.fixtures import synthesize_table
from driftguard.data.licensing import redistribution_decision
from driftguard.data.quality import QUALITY_NOTICE, quality_report, render_markdown
from driftguard.data.registry import TableSpec, get_dataset, load_registry
from tests.data.conftest import ALL_TABLES


@pytest.mark.parametrize(("dataset_id", "table"), ALL_TABLES)
def test_quality_report_runs_for_every_table(dataset_id: str, table: TableSpec) -> None:
    df = synthesize_table(table, n=300, seed=1)
    report = quality_report(df, table, dataset_id)
    assert report.notice == QUALITY_NOTICE
    assert report.n_rows == 300
    assert report.schema_report.ok
    assert sum(report.label_counts.values()) == 300
    assert set(report.private_columns_present) == set(table.private_columns) & set(df.columns)
    assert "Leakage indicators" in render_markdown(report)


def test_duplicates_conflicts_and_constants(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=100, seed=2)
    df = pd.concat([df, df.iloc[[0, 1]]], ignore_index=True)  # two exact duplicates
    conflict = df.iloc[[2]].copy()
    conflict[ton_table.label_column] = 1 - conflict[ton_table.label_column]
    df = pd.concat([df, conflict], ignore_index=True)
    df["missed_bytes"] = 0
    report = quality_report(df, ton_table, "ton_iot")
    assert report.exact_duplicate_rows == 2
    assert report.feature_duplicate_rows >= 3
    assert report.conflicting_label_groups >= 1
    assert "missed_bytes" in report.constant_columns


def test_planted_leaky_column_is_flagged(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=400, seed=3)
    df["service"] = df[ton_table.label_column].map({0: "dns", 1: "http"})
    report = quality_report(df, ton_table, "ton_iot")
    flagged = {c.column for c in report.high_label_purity_columns}
    assert "service" in flagged


def test_timestamp_quality(ton_table: TableSpec) -> None:
    df = synthesize_table(ton_table, n=100, seed=4)
    report = quality_report(df, ton_table, "ton_iot")
    assert report.timestamp is not None
    assert report.timestamp.parse_rate == 1.0
    assert report.timestamp.monotonic_fraction == 1.0
    shuffled = quality_report(df.sample(frac=1, random_state=0), ton_table, "ton_iot")
    assert shuffled.timestamp is not None
    assert shuffled.timestamp.monotonic_fraction is not None
    assert shuffled.timestamp.monotonic_fraction < 1.0


def test_raw_data_is_never_redistributable() -> None:
    decision = redistribution_decision(load_registry().values(), "raw_data")
    assert not decision.allowed


def test_derived_artifacts_blocked_until_license_review() -> None:
    decision = redistribution_decision([get_dataset("edge_iiotset")], "derived_artifact")
    assert not decision.allowed
    assert any("requires_review" in r for r in decision.reasons)
    assert not redistribution_decision([], "derived_artifact").allowed


def test_derived_artifacts_allowed_only_when_every_source_permits() -> None:
    card = get_dataset("edge_iiotset")
    lic = card.license.model_copy(update={"derived_artifact_redistribution": "permitted"})
    permitted = card.model_copy(update={"license": lic})
    assert redistribution_decision([permitted], "derived_artifact").allowed
    assert not redistribution_decision(
        [permitted, get_dataset("ton_iot")], "derived_artifact"
    ).allowed
    unverified = permitted.model_copy(
        update={"license": lic.model_copy(update={"verified_on": None})}
    )
    assert not redistribution_decision([unverified], "derived_artifact").allowed
