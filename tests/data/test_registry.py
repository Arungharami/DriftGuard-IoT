from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from pydantic import ValidationError

from driftguard.data.registry import (
    NON_FEATURE_ROLES,
    DatasetCard,
    KaggleSource,
    TableSpec,
    UnknownDatasetError,
    get_dataset,
    load_registry,
)

EXPECTED = {"ton_iot", "wustl_iiot_2021", "edge_iiotset"}


def test_registry_contains_exactly_the_three_study_datasets() -> None:
    assert set(load_registry()) == EXPECTED


@pytest.mark.parametrize("dataset_id", sorted(EXPECTED))
def test_every_card_has_verified_provenance(dataset_id: str) -> None:
    card = get_dataset(dataset_id)
    assert card.license.verified, "license facts must carry a verification date"
    assert card.license.source_url.scheme in {"http", "https"}
    assert card.license.attribution_required
    assert card.citations
    # No card may claim derived-artifact redistribution without a completed review.
    assert card.license.derived_artifact_redistribution == "requires_review"


@pytest.mark.parametrize("dataset_id", sorted(EXPECTED))
def test_tables_have_consistent_roles(dataset_id: str) -> None:
    for table in get_dataset(dataset_id).tables:
        assert table.label_column not in table.feature_columns
        for name in table.private_columns:
            assert name not in table.feature_columns
        for col in table.columns:
            if col.role in NON_FEATURE_ROLES:
                assert col.name not in table.feature_columns


def test_only_first_party_kaggle_sources_are_approved() -> None:
    for card in load_registry().values():
        source = card.acquisition.kaggle
        if source is not None and source.approved:
            assert source.first_party
    assert get_dataset("ton_iot").acquisition.kaggle is None
    assert get_dataset("wustl_iiot_2021").acquisition.kaggle is None
    assert get_dataset("edge_iiotset").acquisition.method == "kaggle"


def test_wustl_card_matches_publisher_facts() -> None:
    table = get_dataset("wustl_iiot_2021").table()
    # Publisher: 41 features after removing six leaky columns.
    assert len(table.feature_columns) == 41
    leaky = {"StartTime", "LastTime", "SrcAddr", "DstAddr", "sIpId", "dIpId"}
    assert leaky.isdisjoint(table.feature_columns)
    for name in leaky:
        assert table.column(name).exclude_reason is not None
    assert (table.label_column, table.attack_type_column) == ("Target", "Traffic")


def test_recorded_fingerprints_are_not_invented() -> None:
    # Fingerprints are recorded only after a reviewed download; none exist yet.
    for card in load_registry().values():
        for table in card.tables:
            assert table.sha256 is None or len(table.sha256) == 64


def test_unknown_dataset() -> None:
    with pytest.raises(UnknownDatasetError, match="known"):
        get_dataset("unsw_nb15")


def _table(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "t",
        "filename": "t.csv",
        "description": "d",
        "schema_status": "provisional",
        "schema_source": "s",
        "columns": [
            {"name": "x", "dtype": "float"},
            {"name": "y", "dtype": "int", "role": "label"},
        ],
    }
    return {**base, **overrides}


def test_table_rejects_duplicate_columns_and_label_count() -> None:
    cols = [{"name": "x", "dtype": "float"}, {"name": "x", "dtype": "int", "role": "label"}]
    with pytest.raises(ValidationError, match="duplicate"):
        TableSpec.model_validate(_table(columns=cols))
    no_label = [{"name": "x", "dtype": "float"}, {"name": "z", "dtype": "float"}]
    with pytest.raises(ValidationError, match="label"):
        TableSpec.model_validate(_table(columns=no_label))


def test_third_party_kaggle_mirror_cannot_be_approved() -> None:
    with pytest.raises(ValidationError, match="first-party"):
        KaggleSource(
            slug="someone/mirror",
            first_party=False,
            approved=True,
            license_name="MIT",
            verified_on=dt.date(2026, 9, 22),
        )


def test_kaggle_method_requires_approved_source() -> None:
    card = get_dataset("ton_iot").model_dump(mode="json")
    card["acquisition"]["method"] = "kaggle"
    with pytest.raises(ValidationError, match="approved first-party"):
        DatasetCard.model_validate(card)
