"""Synthetic tables that follow a registry schema exactly (column names, order, roles).

They let tests and CI exercise schema validation, quality reports and sampling for every
registered dataset without any real data. The values are random and carry no information
about the real datasets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from driftguard.data.registry import ColumnSpec, TableSpec

SYNTHETIC_CATEGORIES = ("alpha", "beta", "gamma")
SYNTHETIC_ATTACKS = ("normal", "attack_a", "attack_b")


def _column(
    spec: ColumnSpec, n: int, rng: np.random.Generator, attack_idx: np.ndarray
) -> np.ndarray:
    if spec.role == "label":
        return np.where(attack_idx > 0, 1, 0)
    if spec.role == "attack_type":
        return np.take(np.asarray(SYNTHETIC_ATTACKS, dtype=object), attack_idx)
    if spec.role == "timestamp":
        return (1_600_000_000 + np.cumsum(rng.integers(0, 3, size=n))).astype(np.int64)
    if spec.role in {"identifier", "payload"}:
        if spec.dtype in {"int", "float"}:
            return rng.integers(1024, 65535, size=n)
        return np.asarray([f"syn-{spec.role}-{i % 17}" for i in range(n)], dtype=object)
    if spec.dtype == "int":
        return rng.integers(0, 1000, size=n)
    if spec.dtype == "float":
        return np.round(rng.gamma(2.0, 3.0, size=n) + attack_idx * 2.0, 4)
    if spec.dtype == "bool":
        return rng.integers(0, 2, size=n)
    return np.asarray(SYNTHETIC_CATEGORIES, dtype=object)[rng.integers(0, 3, size=n)]


def synthesize_table(
    table: TableSpec, n: int, seed: int, include_optional: bool = False
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    attack_idx = rng.choice(len(SYNTHETIC_ATTACKS), size=n, p=[0.8, 0.15, 0.05])
    attack_idx[: len(SYNTHETIC_ATTACKS)] = np.arange(len(SYNTHETIC_ATTACKS))
    cols = [c for c in table.columns if include_optional or not c.optional]
    df = pd.DataFrame({c.name: _column(c, n, rng, attack_idx) for c in cols})
    df.attrs["driftguard_synthetic"] = True
    return df
