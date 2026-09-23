"""Conditional, class-stratified holdout intervals; never an iid claim for flow captures."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import f1_score


def stratified_f1_interval(
    truth: Any, prediction: Any, *, repeats: int, seed: int
) -> dict[str, Any]:
    truth, prediction = np.asarray(truth), np.asarray(prediction)
    if truth.ndim != 1 or truth.shape != prediction.shape or not len(truth) or repeats < 100:
        raise ValueError("nonempty equal one-dimensional labels and >=100 replicates required")
    classes = np.unique(truth)
    if not set(np.unique(prediction)).issubset(classes):
        raise ValueError("prediction has classes absent from holdout; declare a larger design")
    groups = [np.flatnonzero(truth == label) for label in classes]
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(repeats):
        indices = np.concatenate([rng.choice(group, len(group)) for group in groups])
        estimates.append(
            f1_score(
                truth[indices],
                prediction[indices],
                labels=classes,
                average="macro",
                zero_division=0,
            )
        )
    low, high = np.quantile(estimates, [0.025, 0.975])
    return {
        "low": float(low),
        "high": float(high),
        "level": 0.95,
        "method": "class_stratified_percentile",
        "repeats": repeats,
        "seed": seed,
        "scope": "conditional on fitted model and observed class counts; not capture-level CI",
    }


def calibration_metrics(truth: Any, proba: Any, classes: Any, *, bins: int = 10) -> dict[str, Any]:
    truth, proba, classes = np.asarray(truth), np.asarray(proba), np.asarray(classes)
    if (
        proba.shape != (len(truth), len(classes))
        or not len(truth)
        or bins < 2
        or not np.isfinite(proba).all()
        or np.any(proba < 0)
        or not np.allclose(proba.sum(axis=1), 1)
        or not set(truth).issubset(classes)
    ):
        raise ValueError("invalid probabilities/classes")
    confidence = proba.max(axis=1)
    correct = classes[proba.argmax(axis=1)] == truth
    bucket = np.minimum((confidence * bins).astype(int), bins - 1)
    ece = sum(
        np.mean(bucket == b) * abs(correct[bucket == b].mean() - confidence[bucket == b].mean())
        for b in range(bins)
        if np.any(bucket == b)
    )
    onehot = (truth[:, None] == classes).astype(float)
    return {
        "ece": float(ece),
        "ece_bins": bins,
        "multiclass_brier": float(np.mean(np.sum((proba - onehot) ** 2, axis=1))),
    }
