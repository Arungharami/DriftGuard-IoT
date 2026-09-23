"""Validate a table (header and values) against its registry ``TableSpec``.

*Errors* mean the data does not match the declared schema: missing required columns,
unexpected columns, or column order drift. *Warnings* flag values that cannot be parsed
as the declared type. A provisional schema that validates without errors against a real
file is the evidence needed to mark it ``confirmed``.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from pydantic import BaseModel, ConfigDict

from driftguard.data.registry import TableSpec

NUMERIC_DTYPES = frozenset({"int", "float"})


class SchemaReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_table: str
    schema_status: str
    n_columns_expected: int
    n_columns_observed: int
    missing_columns: list[str]
    unexpected_columns: list[str]
    order_matches: bool
    type_violations: dict[str, int]
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_header(columns: Sequence[str], table: TableSpec) -> SchemaReport:
    return _report(list(columns), table, type_violations={})


def validate_frame(df: pd.DataFrame, table: TableSpec) -> SchemaReport:
    """Validate header and value types. Values listed in ``na_values`` count as missing."""
    violations: dict[str, int] = {}
    for spec in table.columns:
        if spec.name not in df.columns:
            continue
        series = df[spec.name]
        present = series.dropna()
        if table.na_values:
            present = present[~present.astype(str).isin(table.na_values)]
        if spec.dtype in NUMERIC_DTYPES:
            parsed = pd.to_numeric(present, errors="coerce")
            bad = int(parsed.isna().sum())
            if spec.dtype == "int" and bad == 0 and len(parsed) > 0:
                bad = int((parsed.dropna() % 1 != 0).sum())
        elif spec.dtype == "bool":
            bad = int((~present.astype(str).str.lower().isin(["0", "1", "true", "false"])).sum())
        else:
            bad = 0
        if bad:
            violations[spec.name] = bad
    return _report(list(df.columns), table, type_violations=violations)


def _report(observed: list[str], table: TableSpec, type_violations: dict[str, int]) -> SchemaReport:
    declared = [c.name for c in table.columns]
    observed_set = set(observed)
    missing = [c for c in table.required_columns if c not in observed_set]
    unexpected = [c for c in observed if c not in set(declared)]
    expected_order = [c for c in declared if c in observed_set]
    order_matches = [c for c in observed if c in set(declared)] == expected_order

    errors: list[str] = []
    if missing:
        errors.append(f"missing required columns: {missing}")
    if unexpected:
        errors.append(f"unexpected columns: {unexpected}")
    warnings: list[str] = []
    if not order_matches:
        warnings.append("column order differs from the declared schema")
    for name, count in type_violations.items():
        dtype = table.column(name).dtype
        warnings.append(f"{name}: {count} value(s) not parseable as {dtype}")
    if table.schema_status == "provisional":
        warnings.append("schema is provisional (not yet confirmed against a real header)")

    return SchemaReport(
        dataset_table=table.id,
        schema_status=table.schema_status,
        n_columns_expected=len(declared),
        n_columns_observed=len(observed),
        missing_columns=missing,
        unexpected_columns=unexpected,
        order_matches=order_matches,
        type_violations=type_violations,
        errors=errors,
        warnings=warnings,
    )
