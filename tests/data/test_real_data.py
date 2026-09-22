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
