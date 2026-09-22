"""Point-estimate classification metrics.

Bootstrap confidence intervals, PR-AUC, calibration and false-alarm rates are added in
M3; this module only provides the core, label-based metrics.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    recall_score,
)


def classification_metrics(
    y_true: Sequence[Any], y_pred: Sequence[Any], labels: Sequence[Any]
) -> dict[str, Any]:
    labels = list(labels)
    per_class = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro")),
        "micro_f1": float(f1_score(y_true, y_pred, labels=labels, average="micro")),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "recall_per_class": {str(k): float(v) for k, v in zip(labels, per_class, strict=True)},
        "n_samples": len(y_true),
    }
