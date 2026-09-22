"""Deterministic, stratified development subsets.

Subsets are for bounded development runs only. Research runs use the full tables and the
split protocol in docs/scientific-protocol.md. A subset is reproducible from (source
fingerprint, n, seed, stratify column, min_per_class), which is exactly what its
``subset_id`` hashes.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


class SubsetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n: int
    seed: int
    stratify_column: str | None
    min_per_class: int = 1

    def subset_id(self, source_sha256: str) -> str:
        payload = json.dumps(
            {"source": source_sha256, **self.model_dump()}, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _allocate(counts: pd.Series, n: int, min_per_class: int) -> dict[object, int]:
    """Proportional allocation (largest remainder), each class receiving at least
    ``min(min_per_class, class size)``, never more than the class size, and summing to n."""
    counts = counts.sort_index()
    floor = {k: min(int(v), min_per_class) for k, v in counts.items()}
    remaining = n - sum(floor.values())
    if remaining < 0:
        raise ValueError(
            f"n={n} is smaller than the guaranteed minimum {sum(floor.values())} "
            f"({len(counts)} classes x min_per_class={min_per_class})"
        )
    capacity = {k: int(v) - floor[k] for k, v in counts.items()}
    total_capacity = sum(capacity.values())
    alloc = dict(floor)
    if total_capacity == 0 or remaining == 0:
        return alloc
    exact = {k: remaining * capacity[k] / total_capacity for k in capacity}
    base = {k: min(capacity[k], int(np.floor(v))) for k, v in exact.items()}
    leftover = remaining - sum(base.values())
    order = sorted(capacity, key=lambda k: (-(exact[k] - base[k]), str(k)))
    for k in order:
        if leftover == 0:
            break
        if base[k] < capacity[k]:
            base[k] += 1
            leftover -= 1
    for k in alloc:
        alloc[k] += base[k]
    return alloc


def deterministic_sample(df: pd.DataFrame, spec: SubsetSpec) -> pd.DataFrame:
    """Sample ``spec.n`` rows reproducibly. Original row order (and index) is preserved,
    so a time-ordered source stays time-ordered."""
    if spec.n <= 0:
        raise ValueError("n must be positive")
    if spec.n >= len(df):
        return df.copy()
    rng = np.random.default_rng(spec.seed)
    if spec.stratify_column is None:
        chosen = np.sort(rng.choice(len(df), size=spec.n, replace=False))
        return df.iloc[chosen].copy()

    labels = df[spec.stratify_column]
    if labels.isna().any():
        raise ValueError(f"stratify column {spec.stratify_column!r} contains missing values")
    alloc = _allocate(labels.value_counts(), spec.n, spec.min_per_class)
    positions: list[np.ndarray] = []
    for cls in sorted(alloc, key=str):
        pos = np.flatnonzero((labels == cls).to_numpy())
        positions.append(rng.choice(pos, size=alloc[cls], replace=False))
    chosen = np.sort(np.concatenate(positions))
    return df.iloc[chosen].copy()
