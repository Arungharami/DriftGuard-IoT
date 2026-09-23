"""Point-estimate classification metrics.

Covers the reference study's metrics (per-class precision and recall, micro-F1; Sec. IV)
and the project's primary metrics (macro-F1, balanced accuracy, MCC, per-class recall).
PR-AUC is reported per class only when probability scores exist and the class has at
least ``MIN_POSITIVES_FOR_PR_AUC`` positives. Bootstrap confidence intervals and
calibration are added in M3.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

MIN_POSITIVES_FOR_PR_AUC = 10


def classification_metrics(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    labels: Sequence[Any],
    y_proba: np.ndarray | None = None,
    proba_classes: Sequence[Any] | None = None,
) -> dict[str, Any]:
    labels = list(labels)
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    names = [str(k) for k in labels]
    out: dict[str, Any] = {
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "micro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="micro", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
        ),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "macro_precision": float(
            precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "recall_per_class": dict(zip(names, map(float, r), strict=True)),
        "precision_per_class": dict(zip(names, map(float, p), strict=True)),
        "f1_per_class": dict(zip(names, map(float, f), strict=True)),
        "support_per_class": dict(zip(names, map(int, s), strict=True)),
        "confusion_matrix": {
            "labels": names,
            "matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        },
        "n_samples": len(y_true),
    }
    if y_proba is not None and proba_classes is not None:
        truth = np.asarray(y_true)
        pr_auc: dict[str, float | None] = {}
        for j, cls in enumerate(proba_classes):
            positives = truth == cls
            pr_auc[str(cls)] = (
                float(average_precision_score(positives, y_proba[:, j]))
                if positives.sum() >= MIN_POSITIVES_FOR_PR_AUC
                else None
            )
        out["pr_auc_per_class"] = pr_auc
    return out
