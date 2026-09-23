"""Checks against locally downloaded datasets. Never run in CI (``-m "not real_data"``).

Run with ``pytest -m real_data`` after acquiring the data. They skip when files are absent.
"""

from __future__ import annotations

import pytest

from driftguard.data.loader import find_table_file, read_header
from driftguard.data.registry import TableSpec
from driftguard.data.schema import validate_header
from tests.data.conftest import ALL_TABLES


@pytest.mark.real_data
@pytest.mark.parametrize(("dataset_id", "table"), ALL_TABLES)
def test_downloaded_header_matches_registry(dataset_id: str, table: TableSpec) -> None:
    try:
        path = find_table_file(dataset_id, table)
    except FileNotFoundError:
        pytest.skip(f"{dataset_id}/{table.filename} not downloaded")
    report = validate_header(read_header(path), table)
    assert report.ok, report.errors


@pytest.mark.real_data
@pytest.mark.parametrize("dataset_id", ["ton_iot", "wustl_iiot_2021", "edge_iiotset"])
def test_downloaded_file_matches_registry_fingerprint(dataset_id: str) -> None:
    from driftguard.data.registry import get_dataset
    from driftguard.reporting.provenance import sha256_file

    table = get_dataset(dataset_id).table()
    try:
        path = find_table_file(dataset_id, table)
    except FileNotFoundError:
        pytest.skip(f"{dataset_id} not downloaded")
    if table.sha256 is None:
        pytest.skip(f"{dataset_id}: no fingerprint recorded yet")
    assert sha256_file(path) == table.sha256


@pytest.mark.real_data
@pytest.mark.parametrize("dataset_id", ["wustl_iiot_2021", "edge_iiotset", "ton_iot"])
def test_paper_mi_universe_matches_paper_figure(dataset_id: str) -> None:
    """The paper's MI feature universe (numeric columns minus label/pre-MI drops) must equal
    the features shown in its MI figure (Figs. 2-4)."""
    from driftguard.data.loader import read_table
    from driftguard.data.registry import get_dataset
    from driftguard.preprocessing.paper_protocol import PAPER_PROTOCOLS
    from driftguard.preprocessing.protocols import paper_mi_universe

    table = get_dataset(dataset_id).table()
    try:
        path = find_table_file(dataset_id, table)
    except FileNotFoundError:
        pytest.skip(f"{dataset_id} not downloaded")
    protocol = PAPER_PROTOCOLS[dataset_id]
    universe = paper_mi_universe(read_table(path, table), protocol)
    assert set(universe) == set(protocol.figure_mi_features)
