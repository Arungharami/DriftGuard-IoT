"""Deterministic synthetic integration exercise; never a research result/export."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

from driftguard.m5.evaluation import (
    assert_unknown_withheld,
    benchmark_predict,
    defensive_corruption,
    delayed_prequential,
    frozen_transfer,
    paired_block_interval,
    shap_stability,
    unknown_metrics,
    unknown_threshold,
)
from driftguard.reporting.provenance import environment_snapshot, sha256_file, utc_timestamp


def run_smoke(output: Path, *, seed: int = 42, explain: bool = False) -> dict[str, Any]:
    config = {
        "seed": seed,
        "rows": 400,
        "features": 4,
        "delay": 10,
        "policy_period": 30,
        "tree_max_depth": 3,
        "bootstrap_repeats": 200,
        "bootstrap_block_size": 10,
        "explain": explain,
        "error_window": 50,
        "error_threshold": 0.3,
        "unknown_false_reject_rate": 0.05,
        "corruption_fraction_train_iqr": 0.01,
        "corruption_mutable_columns": [0, 1],
        "benchmark_warmup": 3,
        "benchmark_repeats": 100,
        "benchmark_batch_size": 32,
        "shap_background": [0, 50],
        "shap_before": [150, 200],
        "shap_after": [250, 300],
        "shap_class": 1,
        "shap_top_k": 2,
    }
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(400, 4))
    y = (x[:, 0] + x[:, 1] > 0).astype(int)
    y[250:] = (x[250:, 0] - x[250:, 1] > 0).astype(int)
    estimator = DecisionTreeClassifier(max_depth=3, random_state=seed)
    stream = {}
    with threadpool_limits(limits=1):
        for policy in ("frozen", "periodic", "error_triggered"):
            stream[policy] = delayed_prequential(
                estimator,
                x[:100],
                y[:100],
                x[150:],
                y[150:],
                initial_time=np.arange(100),
                event_time=np.arange(150, 400),
                label_time=np.arange(150, 400) + 10,
                policy=policy,
                period=30,
            )
        frozen = stream["frozen"]["predictions"]
        intervals = {
            policy: paired_block_interval(
                y[150:],
                frozen,
                stream[policy]["predictions"],
                classes=[0, 1],
                block_size=10,
                repeats=200,
                seed=seed,
            )
            for policy in ("periodic", "error_triggered")
        }
        model = estimator.fit(x[:100], y[:100])
        transfer = frozen_transfer(estimator, x[:100], y[:100], x[150:])
        noise = defensive_corruption(
            model.predict, x[150:], y[150:], x[:100], mutable_columns=[0, 1], seed=seed
        )
        resources = benchmark_predict(model.predict, x[150:182])
        assert_unknown_withheld(["normal", "known"], ["normal", "known"], held_out="unknown")
        # Unknown-score mechanics only: injected synthetic outliers are NOT attack families.
        calibration = np.linalg.norm(x[100:150], axis=1)
        scores = np.concatenate(
            [np.linalg.norm(x[150:200], axis=1), np.linalg.norm(x[200:250] + 4, axis=1)]
        )
        unknown = unknown_metrics(
            scores, np.repeat([0, 1], 50), threshold=unknown_threshold(calibration)
        )
        explanation: dict[str, Any] = {
            "status": "not_run",
            "reason": "optional explain flag absent",
        }
        if explain:
            import shap

            explainer = shap.TreeExplainer(
                model, data=x[:50], feature_perturbation="interventional"
            )
            before = np.asarray(explainer.shap_values(x[150:200]))[:, :, 1]
            after = np.asarray(explainer.shap_values(x[250:300]))[:, :, 1]
            explanation = shap_stability(before, after, feature_names=["a", "b", "c", "d"], top_k=2)
            explanation.update(
                {
                    "method": "TreeExplainer interventional",
                    "class": 1,
                    "background": "initial training rows 0:50",
                }
            )
    result = {
        "schema_version": 1,
        "kind": "smoke",
        "synthetic_data": True,
        "reportable": False,
        "notice": "NON-REPORTABLE synthetic integration exercise; not IoT/IIoT evidence",
        "created_at": utc_timestamp(),
        "config": config,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "environment": environment_snapshot(),
        "processor": platform.processor(),
        "threads": 1,
        "source_sha256": {
            p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))
        },
        "data_sha256": hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest(),
        "partitions": {"initial": [0, 100], "validation": [100, 150], "stream": [150, 400]},
        "paired_ablation_intervals": intervals,
        "noise_sensitivity": noise,
        "unknown_score_smoke": unknown,
        "shap": explanation,
        "resources": resources,
        "frozen_transfer_matches_stream": bool(np.array_equal(transfer, frozen)),
        "stream": {
            policy: {**record, "predictions": record["predictions"].tolist()}
            for policy, record in stream.items()
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "m5-smoke.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result
