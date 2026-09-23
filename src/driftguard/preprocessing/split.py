"""Train/test partitioning performed *before* any fitting.

Every downstream transformer (encoder, scaler, selector, resampler) is fitted on the
``train`` frame only. The ``test`` frame is untouched until final evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    test: pd.DataFrame

    def __post_init__(self) -> None:
        overlap = self.train.index.intersection(self.test.index)
        if len(overlap) > 0:
            raise ValueError(f"train/test index overlap on {len(overlap)} rows")


def stratified_holdout(df: pd.DataFrame, label_column: str, test_size: float, seed: int) -> Split:
    """Random stratified holdout. Appropriate only when rows are exchangeable."""
    train, test = train_test_split(
        df, test_size=test_size, random_state=seed, stratify=df[label_column], shuffle=True
    )
    return Split(train=train, test=test)


def chronological_holdout(df: pd.DataFrame, timestamp_column: str, test_size: float) -> Split:
    """Earliest ``1 - test_size`` of the timeline trains; the latest rows test.

    Rows sharing the boundary timestamp are all assigned to test, so no training row is
    ever later than or simultaneous with a test row.
    """
    ordered = df.sort_values(timestamp_column, kind="stable")
    cut = int(len(ordered) * (1.0 - test_size))
    if cut <= 0 or cut >= len(ordered):
        raise ValueError("test_size leaves an empty train or test partition")
    boundary = ordered[timestamp_column].iloc[cut]
    is_train = ordered[timestamp_column] < boundary
    return Split(train=ordered[is_train], test=ordered[~is_train])
