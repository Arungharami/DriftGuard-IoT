"""DriftGuard-IoT controlled simulation study (CNT 6167 paper).

Uses the repository's own synthetic flow generator and M5 evaluation primitives.
All data are SYNTHETIC; results are a controlled simulation, not TON_IoT/WUSTL/Edge evidence.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from threadpoolctl import threadpool_limits

from driftguard.config import ModelConfig
from driftguard.data.synthetic import NUMERIC_FEATURES, PROTOCOLS, generate_synthetic_flows
from driftguard.drift.assessment import assess_alarms
from driftguard.m5.evaluation import (
    benchmark_predict,
    defensive_corruption,
    delayed_prequential,
    paired_block_interval,
    shap_stability,
)
from driftguard.models.factory import build_estimator

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
OUT.mkdir(parents=True, exist_ok=True)

N = 6000            # flows per stream
INIT = 1000         # initial labelled training flows
GAP = 200           # validation gap (unused by the stream, keeps strict separation)
BATCH = 20          # flows sharing one prediction instant (one "tick")
DELAY = 5           # label delay in ticks (= 100 flows)
ONSET = 0.5         # drift onset as fraction of the stream
PERIOD = 500        # periodic policy: refit after 500 new released labels
SEEDS = [11, 22, 33, 44, 55]
MODELS = ["decision_tree", "random_forest", "lightgbm"]
POLICIES = ["frozen", "periodic", "error_triggered", "adwin", "adwin_window"]
WINDOW = 1000       # adwin_window: refit on the most recent 1000 released rows
FEATURES = [*NUMERIC_FEATURES, *[f"proto_{p}" for p in PROTOCOLS]]


def encode(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    x = np.log1p(df[list(NUMERIC_FEATURES)].to_numpy(float))
    onehot = np.stack([(df["proto"] == p).to_numpy(float) for p in PROTOCOLS], axis=1)
    return np.hstack([x, onehot]), df["label"].to_numpy(), sorted(df["label"].unique())


def make_stream(seed: int, scenario: str) -> pd.DataFrame:
    total = INIT + GAP + N
    if scenario == "covariate":
        # Repository generator: src_bytes and mean_iat scaled x3 after onset (P(x) changes).
        onset = (INIT + GAP + int(N * ONSET)) / total
        return generate_synthetic_flows(
            total, seed, drift_onset_fraction=onset, drift_scale_multiplier=3.0,
            drift_features=("src_bytes", "mean_iat"),
        )
    # Concept drift: post-onset flows come from a generator with different class-conditional
    # distributions (P(y|x) changes) while class priors stay the same.
    pre_n = INIT + GAP + int(N * ONSET)
    pre = generate_synthetic_flows(total, seed).iloc[:pre_n]
    post = generate_synthetic_flows(total, seed + 1000).iloc[pre_n:]
    return pd.concat([pre, post], ignore_index=True)


def macro(y, p, labels):
    return float(f1_score(y, p, labels=labels, average="macro", zero_division=0))


def run_cell(seed, scenario, model_name):
    df = make_stream(seed, scenario)
    x, y_str, classes = encode(df)
    lut = {c: i for i, c in enumerate(classes)}
    y = np.array([lut[v] for v in y_str], dtype=float)
    ix, iy = x[:INIT], y[:INIT]
    sx, sy = x[INIT + GAP:], y[INIT + GAP:]
    ticks = np.arange(len(sx)) // BATCH + 1000.0
    est = build_estimator(ModelConfig(name=model_name, params={}), seed=seed)
    onset_idx = int(N * ONSET)
    rows, raw = [], {}
    for policy in POLICIES:
        t0 = time.perf_counter()
        r = delayed_prequential(
            est, ix, iy, sx, sy,
            initial_time=np.arange(INIT, dtype=float), event_time=ticks,
            label_time=ticks + DELAY, policy="adwin" if policy == "adwin_window" else policy,
            period=PERIOD, max_retrain_rows=WINDOW if policy == "adwin_window" else None,
            error_window=200, error_threshold=0.30, detector_delta=0.002,
        )
        wall = time.perf_counter() - t0
        p = r["predictions"]
        alarms_t = [a["at"] for a in r["alarms"]]
        change_t = float(ticks[onset_idx])
        assess = None
        if policy.startswith("adwin"):
            assess = assess_alarms(alarms_t, [change_t], horizon=60.0,
                                   stream_start=float(ticks[0]), stream_end=float(ticks[-1]))
        rows.append({
            "seed": seed, "scenario": scenario, "model": model_name, "policy": policy,
            "f1_pre": macro(sy[:onset_idx], p[:onset_idx], list(range(len(classes)))),
            "f1_post": macro(sy[onset_idx:], p[onset_idx:], list(range(len(classes)))),
            "f1_all": macro(sy, p, list(range(len(classes)))),
            "acc_post": float(np.mean(sy[onset_idx:] == p[onset_idx:])),
            "refits": len(r["updates"]),
            "refit_seconds": float(sum(r["refit_seconds"])),
            "wall_seconds": wall,
            "alarms": len(alarms_t),
            "detect_delay_ticks": None if assess is None else assess["delays"][0],
            "false_alarms": None if assess is None else assess["false_alarm_count"],
        })
        raw[policy] = p
    # Paired temporal bootstrap: each policy vs frozen, post-drift segment.
    for row in rows:
        if row["policy"] == "frozen":
            continue
        ci = paired_block_interval(
            sy[onset_idx:], raw["frozen"][onset_idx:], raw[row["policy"]][onset_idx:],
            classes=list(map(float, range(len(classes)))), block_size=100, repeats=500, seed=seed,
        )
        row.update(delta_f1=ci["estimate"], delta_lo=ci["low"], delta_hi=ci["high"])
    # rolling accuracy trace for figure (seed 11, lightgbm only)
    trace = None
    if seed == SEEDS[0] and model_name == "lightgbm":
        w = 300
        trace = {k: pd.Series((v == sy).astype(float)).rolling(w).mean().tolist() for k, v in raw.items()}
    return rows, trace


def resource_bench():
    df = generate_synthetic_flows(INIT + GAP + N, 11)
    x, y_str, classes = encode(df)
    out = []
    for name in ["decision_tree", "random_forest", "bagging", "stacking", "lightgbm"]:
        est = build_estimator(ModelConfig(name=name, params={"cv": 5} if name == "stacking" else {}), seed=11)
        t0 = time.perf_counter(); est.fit(x[:INIT], y_str[:INIT]); fit_s = time.perf_counter() - t0
        b1 = benchmark_predict(est.predict, x[INIT:INIT + 1], repeats=200)
        b256 = benchmark_predict(est.predict, x[INIT:INIT + 256], repeats=100)
        f1 = macro(y_str[INIT + GAP:], est.predict(x[INIT + GAP:]), classes)
        noise = defensive_corruption(
            lambda a, e=est: np.array([classes.index(v) for v in e.predict(a)]),
            x[INIT + GAP:INIT + GAP + 2000], np.array([classes.index(v) for v in y_str[INIT + GAP:INIT + GAP + 2000]]),
            x[:INIT], mutable_columns=list(range(6)), fraction=0.05, seed=11,
        )
        out.append({
            "model": name, "fit_seconds": fit_s, "size_kb": len(pickle.dumps(est)) / 1024,
            "p50_single_ms": b1["p50"] * 1e3, "p95_single_ms": b1["p95"] * 1e3,
            "p50_batch256_ms": b256["p50"] * 1e3, "throughput_rows_s": b256["throughput_rows_per_second"],
            "macro_f1_static": f1, "noise_disagreement": noise["prediction_disagreement"],
            "noise_acc_drop": noise["clean_accuracy"] - noise["corrupted_accuracy"],
        })
    return out


def shap_analysis():
    import shap
    out = {}
    for scenario in ["covariate", "concept"]:
        df = make_stream(11, scenario)
        x, y_str, classes = encode(df)
        est = build_estimator(ModelConfig(name="lightgbm", params={}), seed=11).fit(x[:INIT], y_str[:INIT])
        expl = shap.TreeExplainer(est, data=x[:200], feature_perturbation="interventional")
        s0 = INIT + GAP
        cls = classes.index("dos")
        before = np.asarray(expl.shap_values(x[s0 + 1000:s0 + 1500]))
        after = np.asarray(expl.shap_values(x[s0 + 4000:s0 + 4500]))
        before, after = before[:, :, cls], after[:, :, cls]
        out[scenario] = shap_stability(before, after, feature_names=FEATURES, top_k=3)
    return out


if __name__ == "__main__":
    all_rows, traces = [], {}
    with threadpool_limits(limits=1):
        for scenario in ["covariate", "concept"]:
            for model_name in MODELS:
                for seed in SEEDS:
                    rows, trace = run_cell(seed, scenario, model_name)
                    all_rows += rows
                    if trace:
                        traces[scenario] = trace
                    print(scenario, model_name, seed, "done", flush=True)
        res = resource_bench()
        shp = shap_analysis()
    pd.DataFrame(all_rows).to_csv(OUT / "stream_results.csv", index=False)
    pd.DataFrame(res).to_csv(OUT / "resource_results.csv", index=False)
    (OUT / "traces.json").write_text(json.dumps(traces))
    (OUT / "shap.json").write_text(json.dumps(shp, indent=2))
    print("ALL DONE")
