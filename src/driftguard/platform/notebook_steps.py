"""Thin notebook entry points; all estimators and experiments live in the package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import ModelConfig, load_experiment_config
from driftguard.m5.evaluation import delayed_prequential, frozen_transfer
from driftguard.platform.campaign import CampaignConfig, run_campaign
from driftguard.reporting.provenance import environment_snapshot

STEPS = (
    "environment_setup",
    "data_validation",
    "baseline_models",
    "cross_domain",
    "drift_detection",
    "adaptive_learning",
    "robustness",
    "explainability",
    "resource_benchmark",
    "final_experiments",
)


def run_step(step: str, root: Path = Path("."), *, output: Path | None = None) -> dict[str, Any]:
    if step not in STEPS:
        raise ValueError("unknown notebook step")
    output = output or root / "experiments" / "notebook-runs"
    output.mkdir(parents=True, exist_ok=True)
    notice = "SYNTHETIC SOFTWARE VALIDATION ONLY; no real research result"
    if step == "environment_setup":
        return {"notice": notice, "environment": environment_snapshot(), "accelerator": "CPU"}
    if step == "data_validation":
        from driftguard.m5.readiness import inventory

        return inventory(root / "data")
    if step in {"baseline_models", "final_experiments"}:
        cfg = load_experiment_config(root / "configs/experiments/m2-leakage_safe-synthetic.yaml")
        raw = cfg.model_dump()
        raw["dataset"]["synthetic"]["n_samples"] = 600
        raw["models"] = [
            ModelConfig(name="decision_tree").model_dump(),
            ModelConfig(name="random_forest", params={"n_estimators": 5}).model_dump(),
            ModelConfig(name="bagging", params={"n_estimators": 3}).model_dump(),
            ModelConfig(
                name="stacking",
                params={"cv": 2, "rf": {"n_estimators": 5}, "mlp": {"max_iter": 30}},
            ).model_dump(),
            ModelConfig(name="lightgbm", params={"n_estimators": 10}).model_dump(),
        ]
        config = type(cfg).model_validate(raw)
        report = run_campaign(
            config,
            output / "campaign",
            CampaignConfig(seeds=[11, 23, 42], bootstrap_repeats=100, max_cells=15),
        )
        return {
            "notice": notice,
            "status": "executed",
            "cells": len(report["cells"]),
            "failed": sum(c["status"] != "complete" for c in report["cells"]),
            "report": str(output / "campaign/campaign.json"),
        }
    if step in {"cross_domain", "drift_detection", "adaptive_learning"}:
        rng = np.random.default_rng(42)
        x = rng.normal(size=(500, 4))
        y = (x[:, 0] > 0).astype(int)
        y[250:] = 1 - y[250:]
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        if step == "cross_domain":
            pred = frozen_transfer(model, x[:100], y[:100], x[100:])
            return {"notice": notice, "predictions": len(pred), "real_pairs": 0}
        runs = {}
        for policy in ("frozen", "periodic", "adwin"):
            result = delayed_prequential(
                model,
                x[:100],
                y[:100],
                x[100:],
                y[100:],
                initial_time=np.arange(100),
                event_time=np.arange(100, 500),
                label_time=np.arange(100, 500) + 10,
                policy=policy,
                max_retrain_rows=200,
            )
            runs[policy] = {
                "alarms": result["alarms"],
                "refit_count": len(result["updates"]),
                "refit_seconds": result["refit_seconds"],
            }
        return {"notice": notice, "policies": runs}
    if step == "resource_benchmark":
        from driftguard.benchmark.isolated import benchmark_bundle
        from driftguard.platform.bundle import prepare_bundle

        report_file = output / "campaign/campaign.json"
        if not report_file.exists():
            run_step("baseline_models", root, output=output)
        import json

        report = json.loads(report_file.read_text())
        cell = next(c for c in report["cells"] if c["status"] == "complete")
        bundle = output / "fixture-bundle"
        if not bundle.exists():
            prepare_bundle((output / "campaign" / cell["manifest"]).parent, "decision_tree", bundle)
        return {"notice": notice, "measurements": benchmark_bundle(bundle)}
    from driftguard.m5.smoke import run_smoke

    result = run_smoke(output / step, explain=step == "explainability")
    return {
        "notice": notice,
        "result": result["shap"] if step == "explainability" else result["noise_sensitivity"],
    }
