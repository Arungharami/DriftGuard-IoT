"""Descriptive data-quality reports for a registry table.

These are descriptive statistics of the *source data*, not model results. They inform
the leakage audit and preprocessing decisions in M2. The leakage indicators are
heuristics that flag columns for human review; they prove nothing on their own.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from driftguard.data.registry import TableSpec
from driftguard.data.schema import SchemaReport, validate_frame

QUALITY_NOTICE = (
    "Descriptive statistics of source data for quality and leakage auditing. Not a model "
    "result. Leakage indicators are heuristics for human review."
)
PURITY_THRESHOLD = 0.99
MAX_CARDINALITY_FRACTION = 0.5


class TimestampQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    parse_rate: float
    monotonic_fraction: float | None
    n_unique: int
    min: str | None
    max: str | None


class ColumnPurity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    label_purity: float
    cardinality: int
    role: str


class DataQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notice: str
    dataset_id: str
    table_id: str
    n_rows: int
    n_columns: int
    rows_read_limit: int | None
    schema_report: SchemaReport
    missing_by_column: dict[str, int]
    exact_duplicate_rows: int
    feature_duplicate_rows: int
    conflicting_label_groups: int
    constant_columns: list[str]
    infinite_values_by_column: dict[str, int]
    label_counts: dict[str, int]
    attack_type_counts: dict[str, int] | None
    timestamp: TimestampQuality | None
    high_label_purity_columns: list[ColumnPurity]
    private_columns_present: list[str]


def _counts(series: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).sort_index().items()}


def _timestamp_quality(series: pd.Series, column: str) -> TimestampQuality:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() >= 0.95:
        parsed: pd.Series = numeric
    else:
        parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    valid = parsed.dropna()
    monotonic = None
    if len(valid) > 1:
        diffs = valid.diff().dropna()
        zero = pd.Timedelta(0) if pd.api.types.is_timedelta64_dtype(diffs) else 0
        monotonic = float((diffs >= zero).mean())
    return TimestampQuality(
        column=column,
        parse_rate=float(parsed.notna().mean()) if len(series) else 0.0,
        monotonic_fraction=monotonic,
        n_unique=int(valid.nunique()),
        min=str(valid.min()) if len(valid) else None,
        max=str(valid.max()) if len(valid) else None,
    )


def label_purity(df: pd.DataFrame, column: str, label: str) -> float:
    """Fraction of rows whose value of ``column`` co-occurs with exactly one label value."""
    per_value = df.groupby(column, dropna=False, observed=True)[label].nunique()
    pure_values = per_value[per_value == 1].index
    return float(df[column].isin(pure_values).mean())


def quality_report(
    df: pd.DataFrame, table: TableSpec, dataset_id: str, rows_read_limit: int | None = None
) -> DataQualityReport:
    label = table.label_column
    present = set(df.columns)
    features = [c for c in table.feature_columns if c in present]

    missing = {c: int(v) for c, v in df.isna().sum().items() if v > 0}
    numeric = df.select_dtypes(include=[np.number])
    infinite = {c: int(v) for c, v in np.isinf(numeric).sum().items() if v > 0}
    # nunique(dropna=False) treats an all-NaN or NaN+single-value column correctly.
    constant = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]  # noqa: PD101

    feature_dups = int(df.duplicated(subset=features).sum()) if features else 0
    conflicts = 0
    if features and label in present:
        per_group = df.groupby(features, dropna=False)[label].nunique()
        conflicts = int((per_group > 1).sum())  # groups with >1 label, not a constancy test

    purity: list[ColumnPurity] = []
    if label in present and len(df) > 0:
        for spec in table.columns:
            if spec.name not in present or spec.role in {"label", "attack_type"}:
                continue
            card = int(df[spec.name].nunique(dropna=False))
            if card < 2 or card > MAX_CARDINALITY_FRACTION * len(df):
                continue
            p = label_purity(df, spec.name, label)
            if p >= PURITY_THRESHOLD:
                purity.append(
                    ColumnPurity(column=spec.name, label_purity=p, cardinality=card, role=spec.role)
                )

    attack = table.attack_type_column
    ts = table.timestamp_column
    return DataQualityReport(
        notice=QUALITY_NOTICE,
        dataset_id=dataset_id,
        table_id=table.id,
        n_rows=len(df),
        n_columns=df.shape[1],
        rows_read_limit=rows_read_limit,
        schema_report=validate_frame(df, table),
        missing_by_column=missing,
        exact_duplicate_rows=int(df.duplicated().sum()),
        feature_duplicate_rows=feature_dups,
        conflicting_label_groups=conflicts,
        constant_columns=constant,
        infinite_values_by_column=infinite,
        label_counts=_counts(df[label]) if label in present else {},
        attack_type_counts=_counts(df[attack]) if attack and attack in present else None,
        timestamp=_timestamp_quality(df[ts], ts) if ts and ts in present else None,
        high_label_purity_columns=sorted(purity, key=lambda c: -c.label_purity),
        private_columns_present=[c for c in table.private_columns if c in present],
    )


def render_markdown(report: DataQualityReport) -> str:
    s = report.schema_report
    lines = [
        f"# Data quality: {report.dataset_id} / {report.table_id}",
        "",
        f"> {report.notice}",
        "",
        f"- Rows: {report.n_rows:,}"
        + (f" (read limit {report.rows_read_limit:,})" if report.rows_read_limit else ""),
        f"- Columns: {report.n_columns} (declared {s.n_columns_expected}, "
        f"schema {s.schema_status})",
        f"- Schema errors: {s.errors or 'none'}",
        f"- Exact duplicate rows: {report.exact_duplicate_rows:,}",
        f"- Duplicate rows on feature columns: {report.feature_duplicate_rows:,}",
        f"- Feature-identical groups with conflicting labels: {report.conflicting_label_groups:,}",
        f"- Constant columns: {report.constant_columns or 'none'}",
        f"- Columns with missing values: {len(report.missing_by_column)}",
        f"- Private columns present (never exposed publicly): {report.private_columns_present}",
        "",
        "## Label counts",
        "",
        *[f"- `{k}`: {v:,}" for k, v in report.label_counts.items()],
    ]
    if report.attack_type_counts is not None:
        lines += ["", "## Attack-type counts", ""]
        lines += [f"- `{k}`: {v:,}" for k, v in report.attack_type_counts.items()]
    if report.timestamp is not None:
        t = report.timestamp
        lines += [
            "",
            "## Timestamp",
            "",
            f"- Column `{t.column}`: parse rate {t.parse_rate:.4f}, monotonic fraction "
            f"{t.monotonic_fraction}, unique {t.n_unique:,}, range {t.min} to {t.max}",
        ]
    lines += ["", "## Leakage indicators (label purity >= 0.99, for review)", ""]
    lines += [
        f"- `{c.column}` ({c.role}): purity {c.label_purity:.4f}, cardinality {c.cardinality:,}"
        for c in report.high_label_purity_columns
    ] or ["- none flagged"]
    return "\n".join(lines) + "\n"
