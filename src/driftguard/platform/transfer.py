"""Explicit numeric semantic contracts; no inferred packet-to-flow equivalence."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from driftguard.data.registry import TableSpec
from driftguard.m5.evaluation import frozen_transfer


class FeatureMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    source: str
    target: str
    unit: str = Field(min_length=1)
    meaning: str = Field(min_length=20)
    source_scale: float = Field(default=1, gt=0, allow_inf_nan=False)
    target_scale: float = Field(default=1, gt=0, allow_inf_nan=False)


class SemanticContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_table: str
    target_table: str
    granularity: str = Field(min_length=10)
    review_reference: str = Field(pattern=r"^https://github.com/Arungharami/DriftGuard-IoT/")
    features: list[FeatureMap] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self) -> SemanticContract:
        for field in ("name", "source", "target"):
            if len({getattr(f, field) for f in self.features}) != len(self.features):
                raise ValueError("semantic map names must be unique")
        return self


def aligned_transfer(
    estimator: Any,
    source: pd.DataFrame,
    labels: Any,
    target: pd.DataFrame,
    source_schema: TableSpec,
    target_schema: TableSpec,
    contract: SemanticContract,
) -> Any:
    if (contract.source_table, contract.target_table) != (source_schema.id, target_schema.id):
        raise ValueError("contract/table mismatch")
    matrices = []
    for frame, schema, side in (
        (source, source_schema, "source"),
        (target, target_schema, "target"),
    ):
        values = []
        for feature in contract.features:
            name = getattr(feature, side)
            spec = schema.column(name)
            if not spec.is_feature or spec.dtype not in {"int", "float"}:
                raise ValueError("only reviewed non-private numeric features may be aligned")
            values.append(
                pd.to_numeric(frame[name], errors="raise").to_numpy()
                * getattr(feature, side + "_scale")
            )
        matrices.append(np.column_stack(values))
    return frozen_transfer(estimator, matrices[0], np.asarray(labels), matrices[1])


def chronological_partition(
    times: Any, groups: Any, *, train_end: float, test_start: float
) -> tuple[Any, Any]:
    times, groups = np.asarray(times, dtype=float), np.asarray(groups)
    if (
        times.ndim != 1
        or groups.shape != times.shape
        or not len(times)
        or not np.isfinite(times).all()
        or np.any(np.diff(times) < 0)
        or not np.isfinite([train_end, test_start]).all()
        or train_end >= test_start
    ):
        raise ValueError(
            "finite ordered genuine timestamps and strictly separated cutoffs required"
        )
    train, test = np.flatnonzero(times <= train_end), np.flatnonzero(times >= test_start)
    if not len(train) or not len(test) or set(groups[train]) & set(groups[test]):
        raise ValueError("empty partition or capture/session crosses temporal boundary")
    return train, test
