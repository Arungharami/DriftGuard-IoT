"""Offline evaluation primitives. No network access, traffic generation, or evasion search.

Callers must supply isolated, semantically aligned partitions. The campaign readiness
check does not certify them; actual M4 alignment and split artifacts are still required.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from sklearn.base import clone
from sklearn.metrics import f1_score, roc_auc_score

Array = NDArray[Any]


def _finite(values: Any, ndim: int) -> Array:
    array = np.asarray(values, dtype=float)
    if array.ndim != ndim or not array.size or not np.isfinite(array).all():
        raise ValueError(f"expected nonempty finite {ndim}-dimensional data")
    return array


def paired_block_interval(
    truth: Array,
    baseline: Array,
    candidate: Array,
    *,
    classes: Sequence[int],
    block_size: int,
    repeats: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    """Paired circular moving-block bootstrap of candidate minus baseline macro-F1.

    Fixed class universe; contiguous order retained within blocks. Block length must
    be preregistered from source validation, never selected for a favorable test CI.
    This conditional test-sample CI does not estimate training-seed uncertainty.
    """
    truth, baseline, candidate = (_finite(v, 1) for v in (truth, baseline, candidate))
    n = len(truth)
    if not (len(baseline) == len(candidate) == n):
        raise ValueError("paired predictions must have equal lengths")
    if not classes or len(set(classes)) != len(classes):
        raise ValueError("classes must be a fixed unique nonempty universe")
    if not all(set(v).issubset(classes) for v in (truth, baseline, candidate)):
        raise ValueError("labels outside the declared class universe")
    if not 1 <= block_size <= n // 2 or repeats < 100:
        raise ValueError("need >=2 blocks and >=100 bootstrap replicates")

    def delta(indices: Array) -> float:
        return float(
            f1_score(
                truth[indices],
                candidate[indices],
                labels=list(classes),
                average="macro",
                zero_division=0,
            )
            - f1_score(
                truth[indices],
                baseline[indices],
                labels=list(classes),
                average="macro",
                zero_division=0,
            )
        )

    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(repeats):
        starts = rng.integers(0, n, size=int(np.ceil(n / block_size)))
        indices = ((starts[:, None] + np.arange(block_size)) % n).ravel()[:n]
        draws.append(delta(indices))
    low, high = np.quantile(draws, [0.025, 0.975])
    return {
        "estimate": delta(np.arange(n)),
        "low": float(low),
        "high": float(high),
        "level": 0.95,
        "method": "paired_circular_moving_block_percentile",
        "block_size": block_size,
        "repeats": repeats,
        "seed": seed,
        "n": n,
        "classes": list(classes),
        "includes_training_uncertainty": False,
    }


def assert_isolated(*partitions: Array) -> None:
    """Reject feature-identical rows across partitions, even with conflicting labels."""
    seen: set[tuple[float, ...]] = set()
    width = None
    for partition in partitions:
        values = _finite(partition, 2)
        if width is not None and values.shape[1] != width:
            raise ValueError("feature widths differ")
        width = values.shape[1]
        rows = {tuple(row) for row in values}
        if seen & rows:
            raise ValueError("feature-identical rows cross partition boundaries")
        seen.update(rows)


def delayed_prequential(
    estimator: Any,
    initial_x: Array,
    initial_y: Array,
    stream_x: Array,
    stream_y: Array,
    *,
    initial_time: Array,
    event_time: Array,
    label_time: Array,
    policy: Literal["frozen", "periodic", "error_triggered"] = "frozen",
    period: int = 50,
    error_window: int = 50,
    error_threshold: float = 0.3,
) -> dict[str, Any]:
    """Predict each timestamp group before revealing even zero-delay labels.

    Refits clone the entire estimator/pipeline using initial data and *only* earlier
    events with labels available strictly before current time. Error-triggered policy
    is a simple development comparator, NOT a validated drift detector. No stream
    labels are used for threshold choice. Initial labels must already be available.
    """
    initial_x, stream_x = (_finite(v, 2) for v in (initial_x, stream_x))
    initial_y, stream_y, initial_time, event_time, label_time = (
        _finite(v, 1) for v in (initial_y, stream_y, initial_time, event_time, label_time)
    )
    if not len(initial_x) == len(initial_y) == len(initial_time):
        raise ValueError("initial lengths differ")
    if not len(stream_x) == len(stream_y) == len(event_time) == len(label_time):
        raise ValueError("stream lengths differ")
    if np.any(np.diff(event_time) < 0) or initial_time.max() >= event_time.min():
        raise ValueError("timestamps must be chronological with strict initial separation")
    if np.any(label_time < event_time):
        raise ValueError("labels cannot arrive before events")
    if policy not in {"frozen", "periodic", "error_triggered"}:
        raise ValueError("unknown adaptation policy")
    if period < 1 or error_window < 1 or not 0 <= error_threshold <= 1:
        raise ValueError("invalid policy configuration")
    assert_isolated(initial_x, stream_x)
    model = clone(estimator).fit(initial_x, initial_y)
    predictions = np.empty(len(stream_y), dtype=initial_y.dtype)
    updates: list[dict[str, Any]] = []
    used = 0
    for now in np.unique(event_time):
        current = np.flatnonzero(event_time == now)
        available = np.flatnonzero((event_time < now) & (label_time < now))
        # Latest released observations, not latest future truth.
        ordered = available[np.argsort(label_time[available], kind="stable")]
        fresh = len(available) - used
        trigger = policy == "periodic" and fresh >= period
        if policy == "error_triggered" and fresh >= error_window:
            recent = ordered[-error_window:]
            trigger = bool(np.mean(predictions[recent] != stream_y[recent]) > error_threshold)
        if trigger:
            model = clone(estimator).fit(
                np.concatenate([initial_x, stream_x[available]]),
                np.concatenate([initial_y, stream_y[available]]),
            )
            used = len(available)
            updates.append({"at": float(now), "released_indices": available.tolist()})
        predictions[current] = model.predict(stream_x[current])
    return {
        "predictions": predictions,
        "updates": updates,
        "policy": policy,
        "unreleased_at_end": int(np.sum(label_time >= event_time[-1])),
    }


def unknown_threshold(known_validation_scores: Array, *, false_reject_rate: float = 0.05) -> float:
    """High score means unknown; calibrate exclusively on known source validation."""
    scores = _finite(known_validation_scores, 1)
    if not 0 < false_reject_rate < 1:
        raise ValueError("false rejection rate must be between zero and one")
    return float(np.quantile(scores, 1 - false_reject_rate, method="higher"))


def unknown_metrics(scores: Array, is_unknown: Array, *, threshold: float) -> dict[str, float]:
    scores, labels = _finite(scores, 1), _finite(is_unknown, 1)
    if len(scores) != len(labels) or set(labels) != {0, 1} or not np.isfinite(threshold):
        raise ValueError("both known and unknown examples and a finite threshold are required")
    rejected = scores > threshold
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        "unknown_recall": float(rejected[labels == 1].mean()),
        "known_false_reject_rate": float(rejected[labels == 0].mean()),
        "threshold": threshold,
    }


def defensive_corruption(
    predict: Callable[[Array], Array],
    evaluation_x: Array,
    truth: Array,
    training_x: Array,
    *,
    mutable_columns: Sequence[int],
    fraction: float = 0.01,
    seed: int = 42,
) -> dict[str, float | int]:
    """Aggregate-only bounded sensor-noise test; no optimization or exported samples.

    Opt-in continuous independent measurements only. Train IQR defines noise scale;
    original +/- fraction*IQR bounds each value. Physical/relational validity remains
    the caller's schema obligation. This is sensitivity, not an evasion guarantee.
    """
    original, train = (_finite(v, 2) for v in (evaluation_x, training_x))
    labels = _finite(truth, 1)
    if original.shape[1] != train.shape[1] or len(labels) != len(original):
        raise ValueError("incompatible dimensions")
    if len(original) > 10000 or not 0 <= fraction <= 0.05:
        raise ValueError("offline budget: <=10000 rows and fraction <=0.05")
    cols = list(mutable_columns)
    if not cols or len(set(cols)) != len(cols) or any(c < 0 or c >= train.shape[1] for c in cols):
        raise ValueError("explicit unique mutable columns required")
    scale = np.subtract(*np.percentile(train[:, cols], [75, 25], axis=0))
    perturbed = original.copy()
    rng = np.random.default_rng(seed)
    perturbed[:, cols] += rng.uniform(-1, 1, (len(original), len(cols))) * scale * fraction
    clean, noisy = np.asarray(predict(original)), np.asarray(predict(perturbed))
    if clean.shape != labels.shape or noisy.shape != labels.shape:
        raise ValueError("prediction shape mismatch")
    return {
        "rows": len(original),
        "fraction_train_iqr": fraction,
        "seed": seed,
        "clean_accuracy": float(np.mean(clean == labels)),
        "corrupted_accuracy": float(np.mean(noisy == labels)),
        "prediction_disagreement": float(np.mean(clean != noisy)),
    }


def shap_stability(
    before: Array, after: Array, *, feature_names: Sequence[str], top_k: int
) -> dict[str, Any]:
    """Compare actual SHAP matrices for one fixed output class, in identical feature order.

    Ties at the top-k boundary are included; no arbitrary feature-order tie breaking.
    All-zero importance yields an undefined result rather than invented stability.
    """
    before, after = _finite(before, 2), _finite(after, 2)
    n = len(feature_names)
    if before.shape[1] != n or after.shape[1] != n or len(set(feature_names)) != n:
        raise ValueError("SHAP feature schemas differ")
    if not 1 <= top_k <= n:
        raise ValueError("invalid top_k")
    a, b = np.abs(before).mean(axis=0), np.abs(after).mean(axis=0)
    if not a.any() or not b.any():
        return {"status": "undefined", "reason": "all-zero importance"}
    a_set = set(np.flatnonzero(a >= np.sort(a)[-top_k]))
    b_set = set(np.flatnonzero(b >= np.sort(b)[-top_k]))
    return {
        "status": "measured",
        "top_k": top_k,
        "jaccard": len(a_set & b_set) / len(a_set | b_set),
        "before": dict(zip(feature_names, a.tolist(), strict=True)),
        "after": dict(zip(feature_names, b.tolist(), strict=True)),
        "ties_included": True,
    }


def benchmark_predict(
    predict: Callable[[Array], Any], batch: Array, *, repeats: int = 100
) -> dict[str, Any]:
    """Warm inference batch timings; caller must report hardware and thread limits."""
    batch = _finite(batch, 2)
    if not 10 <= repeats <= 10000:
        raise ValueError("benchmark repeats must be between 10 and 10000")
    for _ in range(3):
        predict(batch)
    times = []
    cpu_start = time.process_time()
    for _ in range(repeats):
        start = time.perf_counter_ns()
        predict(batch)
        times.append((time.perf_counter_ns() - start) / 1e9)
    cpu = time.process_time() - cpu_start
    return {
        "batch_size": len(batch),
        "repeats": repeats,
        "warmup": 3,
        "latency_unit": "seconds_per_batch",
        "p50": float(np.quantile(times, 0.5)),
        "p95": float(np.quantile(times, 0.95)),
        "p99": float(np.quantile(times, 0.99)),
        "throughput_rows_per_second": len(batch) * repeats / sum(times),
        "process_cpu_seconds": cpu,
        "peak_rss": None,
        "peak_rss_note": "requires isolated process measurement",
    }


def frozen_transfer(
    estimator: Any,
    source_x: Array,
    source_y: Array,
    target_x: Array,
) -> Array:
    """Fit a fresh full pipeline on source only and predict an already aligned target.

    Low-level primitive, not dataset/schema certification. Target labels are deliberately
    absent from this interface. No target adaptation or target hyperparameter selection.
    """
    source_x, target_x = _finite(source_x, 2), _finite(target_x, 2)
    source_y = _finite(source_y, 1)
    if len(source_x) != len(source_y) or len(np.unique(source_y)) < 2:
        raise ValueError("source requires aligned labels and at least two classes")
    assert_isolated(source_x, target_x)
    return np.asarray(clone(estimator).fit(source_x, source_y).predict(target_x))


def assert_unknown_withheld(
    training_families: Sequence[str],
    validation_families: Sequence[str],
    *,
    held_out: str,
) -> None:
    """Reject held-out attack exposure in training or threshold/hyperparameter validation."""
    if not held_out or not training_families or not validation_families:
        raise ValueError("explicit nonempty family partitions required")
    if held_out in training_families or held_out in validation_families:
        raise ValueError("held-out attack family leaked into development partitions")
