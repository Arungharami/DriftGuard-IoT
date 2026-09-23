"""Duplicate and target-leakage audit for a specific train/test split (M2).

M1's ``driftguard.data.quality`` already computes descriptive leakage *indicators*
(duplicate counts, label-purity heuristics) on a single, pre-split table - see
``docs/milestones.md``: "Descriptive indicators implemented (M1 quality report); audit
decisions M2." This module adds what only makes sense once a split exists (whether any
row's features leaked across the train/test boundary) and turns the M1 indicators into
an actual, justified feature-exclusion *decision* - computed from the training partition
only, so the decision itself never depends on test data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from driftguard.data.quality import PURITY_THRESHOLD, label_purity

AUDIT_NOTICE = (
    "Duplicate and target-leakage audit for one train/test split. Column exclusion "
    "decisions are computed from the training partition only. Heuristics for human "
    "review, not proof of a leakage-free pipeline."
)


@dataclass(frozen=True)
class LeakageAuditReport:
    notice: str
    n_train: int
    n_test: int
    exact_duplicate_rows_train: int
    exact_duplicate_rows_test: int
    cross_partition_duplicate_rows: int
    high_purity_columns: dict[str, float]
    identifier_columns: tuple[str, ...]
    excluded_columns: tuple[str, ...]
    exclusion_reasons: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "notice": self.notice,
            "n_train": self.n_train,
            "n_test": self.n_test,
            "exact_duplicate_rows_train": self.exact_duplicate_rows_train,
            "exact_duplicate_rows_test": self.exact_duplicate_rows_test,
            "cross_partition_duplicate_rows": self.cross_partition_duplicate_rows,
            "high_purity_columns": self.high_purity_columns,
            "identifier_columns": list(self.identifier_columns),
            "excluded_columns": list(self.excluded_columns),
            "exclusion_reasons": self.exclusion_reasons,
        }


def _row_hashes(df: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    return pd.util.hash_pandas_object(df[list(columns)], index=False)


def audit_leakage(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: Sequence[str],
    label_column: str,
    identifier_columns: Sequence[str] = (),
    purity_threshold: float = PURITY_THRESHOLD,
) -> LeakageAuditReport:
    """Audit one already-performed train/test split.

    ``identifier_columns`` are columns the caller has already decided are identifiers
    (IPs, MACs, raw timestamps, host-acting ports - docs/scientific-protocol.md §3.6),
    always excluded regardless of measured purity. ``feature_columns`` should be the
    full candidate feature set *before* that exclusion, so purity is measured on
    everything, including columns that will end up excluded for other reasons - the
    report is diagnostic even for columns already excluded by policy.
    """
    features = list(feature_columns)
    id_cols = set(identifier_columns)

    exact_train = int(train.duplicated(subset=features).sum())
    exact_test = int(test.duplicated(subset=features).sum())

    train_hashes = set(_row_hashes(train, features))
    test_hashes = _row_hashes(test, features)
    cross_partition = int(test_hashes.isin(train_hashes).sum())

    high_purity: dict[str, float] = {}
    for column in features:
        if column in id_cols or column == label_column:
            continue
        cardinality = int(train[column].nunique(dropna=False))
        if cardinality < 2 or cardinality > 0.5 * len(train):
            continue
        purity = label_purity(train, column, label_column)
        if purity >= purity_threshold:
            high_purity[column] = purity

    reasons: dict[str, str] = {}
    for column in identifier_columns:
        reasons[column] = "identifier column (IP/MAC/port/raw timestamp) per protocol §3.6"
    for column, purity in high_purity.items():
        reasons[column] = f"label purity {purity:.4f} >= threshold {purity_threshold} on train"

    excluded = tuple(sorted(set(identifier_columns) | set(high_purity)))

    return LeakageAuditReport(
        notice=AUDIT_NOTICE,
        n_train=len(train),
        n_test=len(test),
        exact_duplicate_rows_train=exact_train,
        exact_duplicate_rows_test=exact_test,
        cross_partition_duplicate_rows=cross_partition,
        high_purity_columns=high_purity,
        identifier_columns=tuple(identifier_columns),
        excluded_columns=excluded,
        exclusion_reasons=reasons,
    )
