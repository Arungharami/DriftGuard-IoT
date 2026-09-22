"""Locate and read registry tables from local storage.

The data root defaults to ``./data`` and can be overridden with ``DRIFTGUARD_DATA_ROOT``.
Raw files live under ``<root>/raw/<dataset_id>/`` in any sub-directory layout.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from driftguard.data.registry import TableSpec

DATA_ROOT_ENV = "DRIFTGUARD_DATA_ROOT"


def data_root() -> Path:
    return Path(os.environ.get(DATA_ROOT_ENV, "data"))


def raw_dir(dataset_id: str, root: Path | None = None) -> Path:
    return (root or data_root()) / "raw" / dataset_id


def find_table_file(dataset_id: str, table: TableSpec, root: Path | None = None) -> Path:
    """Find the table's file under the dataset's raw directory (exactly one match required)."""
    base = raw_dir(dataset_id, root)
    if table.relative_path and (base / table.relative_path).is_file():
        return base / table.relative_path
    matches = sorted(p for p in base.rglob(table.filename) if p.is_file())
    if not matches:
        raise FileNotFoundError(
            f"{table.filename} not found under {base}. See `driftguard data show {dataset_id}` "
            "for acquisition instructions."
        )
    if len(matches) > 1:
        raise FileExistsError(f"multiple candidates for {table.filename}: {matches}")
    return matches[0]


def read_header(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def read_table(path: Path, table: TableSpec, nrows: int | None = None) -> pd.DataFrame:
    """Read a CSV table. ``nrows`` bounds development runs; ``None`` reads everything.

    Values are kept as read; only the declared ``na_values`` become missing. Type coercion
    is left to preprocessing (M2) so that quality reports see the raw values.
    """
    return pd.read_csv(
        path,
        nrows=nrows,
        na_values=table.na_values or None,
        keep_default_na=True,
        low_memory=False,
    )
