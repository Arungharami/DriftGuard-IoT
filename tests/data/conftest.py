from __future__ import annotations

import pytest

from driftguard.data.registry import TableSpec, load_registry

ALL_TABLES = [
    pytest.param(card.id, table, id=f"{card.id}:{table.id}")
    for card in load_registry().values()
    for table in card.tables
]


@pytest.fixture
def ton_table() -> TableSpec:
    return load_registry()["ton_iot"].table()
