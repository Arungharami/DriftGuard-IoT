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
    precision_score,
    recall_score,
)


def classification_metrics(
    y_true: Sequence[Any], y_pred: Sequence[Any], labels: Sequence[Any]
) -> dict[str, Any]:
    labels = list(labels)
    recall_per_class = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    precision_per_class = precision_score(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro")),
        "micro_f1": float(f1_score(y_true, y_pred, labels=labels, average="micro")),
        # macro_precision/macro_recall alongside micro_f1 line up with the reference
        # paper's reported metrics (Precision, Recall, Micro-F1 - see
        # paper/methodology.md); macro_f1 remains this project's own primary metric
        # per docs/scientific-protocol.md §6.
        "macro_precision": float(
            precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "recall_per_class": {
            str(k): float(v) for k, v in zip(labels, recall_per_class, strict=True)
        },
        "precision_per_class": {
            str(k): float(v) for k, v in zip(labels, precision_per_class, strict=True)
        },
        "n_samples": len(y_true),
    }
