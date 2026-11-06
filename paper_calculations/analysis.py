"""Summaries and result figures for the paper."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
FIG = Path(sys.argv[2] if len(sys.argv) > 2 else "figures")
FIG.mkdir(exist_ok=True)
df = pd.read_csv(RES / "stream_results.csv")
order = ["frozen", "periodic", "error_triggered", "adwin", "adwin_window"]
names = {"frozen": "Frozen", "periodic": "Periodic", "error_triggered": "Error-threshold",
         "adwin": "ADWIN", "adwin_window": "ADWIN-window"}
mnames = {"decision_tree": "Decision Tree", "random_forest": "Random Forest", "lightgbm": "LightGBM"}

g = df.groupby(["scenario", "model", "policy"])
summ = g.agg(f1_pre=("f1_pre", "mean"), f1_post=("f1_post", "mean"), f1_post_sd=("f1_post", "std"),
             delta=("delta_f1", "mean"), delta_sd=("delta_f1", "std"),
             ci_excl0=("delta_lo", lambda s: int((s > 0).sum())),
             refits=("refits", "mean"), refit_s=("refit_seconds", "mean"),
             alarms=("alarms", "mean"), delay=("detect_delay_ticks", "mean"),
             fa=("false_alarms", "mean")).reset_index()
summ.to_csv(RES / "summary_by_cell.csv", index=False)
pd.set_option("display.width", 200)
print(summ.round(3).to_string())

# averaged over models
pol = df.groupby(["scenario", "policy"]).agg(
    f1_post=("f1_post", "mean"), f1_post_sd=("f1_post", "std"), refits=("refits", "mean"),
    refit_s=("refit_seconds", "mean"), delta=("delta_f1", "mean")).reset_index()
print(pol.round(3).to_string())
pol.to_csv(RES / "summary_by_policy.csv", index=False)

# share of post-drift loss recovered relative to periodic, per scenario/model
rec = []
for (sc, m), sub in summ.groupby(["scenario", "model"]):
    s = sub.set_index("policy")
    fz, pe = s.loc["frozen", "f1_post"], s.loc["periodic", "f1_post"]
    for p in ["adwin", "adwin_window", "error_triggered"]:
        rec.append({"scenario": sc, "model": m, "policy": p,
                    "gain_vs_periodic_gain": (s.loc[p, "f1_post"] - fz) / (pe - fz) if pe != fz else np.nan,
                    "refit_seconds_ratio": s.loc[p, "refit_s"] / s.loc["periodic", "refit_s"]})
rec = pd.DataFrame(rec); rec.to_csv(RES / "recovery.csv", index=False)
print(rec.round(3).to_string())

# ---- Fig 4: post-drift macro-F1 by policy, model, scenario
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200, sharey=True)
colors = ["#7f8c8d", "#2e86c1", "#e67e22", "#8e44ad", "#27ae60"]
for ax, sc in zip(axes, ["covariate", "concept"]):
    sub = summ[summ.scenario == sc]
    x = np.arange(3); w = 0.16
    for i, p in enumerate(order):
        vals = [sub[(sub.model == m) & (sub.policy == p)].f1_post.item() for m in mnames]
        sds = [sub[(sub.model == m) & (sub.policy == p)].f1_post_sd.item() for m in mnames]
        ax.bar(x + (i - 2) * w, vals, w, yerr=sds, capsize=2, color=colors[i], label=names[p],
               error_kw=dict(lw=0.8))
    ax.set_xticks(x, list(mnames.values()))
    ax.set_title(f"{'Covariate' if sc == 'covariate' else 'Concept'} drift", fontsize=11)
    ax.grid(axis="y", alpha=0.3); ax.set_ylim(0, 1)
axes[0].set_ylabel("Post-drift macro-F1 (mean ± SD, 5 seeds)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, fontsize=9, frameon=False)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "fig_f1_post.png"); plt.close(fig)

# ---- Fig 5: rolling accuracy traces (LightGBM, seed 11)
tr = json.loads((RES / "traces.json").read_text())
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), dpi=200, sharey=True)
for ax, sc in zip(axes, ["covariate", "concept"]):
    for i, p in enumerate(order):
        y = np.array(tr[sc][p], dtype=float)
        ax.plot(np.arange(len(y)), y, color=colors[i], lw=1.2, label=names[p])
    ax.axvline(3000, color="black", ls="--", lw=1); ax.text(3050, 0.32, "drift onset", fontsize=8)
    ax.set_title(f"{'Covariate' if sc == 'covariate' else 'Concept'} drift (LightGBM, seed 11)", fontsize=10)
    ax.set_xlabel("Flow index in stream"); ax.grid(alpha=0.3); ax.set_ylim(0.3, 1.0)
axes[0].set_ylabel("Rolling accuracy (300 flows)")
axes[1].legend(fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(FIG / "fig_traces.png"); plt.close(fig)

# ---- Fig 6: cost vs benefit (concept drift)
fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=200)
marks = {"decision_tree": "o", "random_forest": "s", "lightgbm": "^"}
for sc, fill in [("concept", True), ("covariate", False)]:
    sub = summ[summ.scenario == sc]
    for i, p in enumerate(order[1:], start=1):
        for m in mnames:
            r = sub[(sub.model == m) & (sub.policy == p)].iloc[0]
            ax.scatter(r.refit_s + 1e-3, r.delta, marker=marks[m], s=45,
                       facecolor=colors[i] if fill else "white", edgecolor=colors[i], lw=1.3)
ax.set_xscale("log"); ax.axhline(0, color="black", lw=0.7)
ax.set_xlabel("Total retraining time per stream (s, log scale)")
ax.set_ylabel("Post-drift macro-F1 gain over frozen")
from matplotlib.lines import Line2D
h = [Line2D([], [], marker="o", ls="", color=colors[i], label=names[p]) for i, p in enumerate(order) if i]
h += [Line2D([], [], marker=marks[m], ls="", color="gray", label=mnames[m]) for m in mnames]
h += [Line2D([], [], marker="o", ls="", mfc="white", color="gray", label="open = covariate")]
ax.legend(handles=h, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1)); ax.grid(alpha=0.3)
ax.text(1.2e-3, 0.012, "no refit", fontsize=7, color="gray")
fig.tight_layout(); fig.savefig(FIG / "fig_cost_benefit.png"); plt.close(fig)

res = pd.read_csv(RES / "resource_results.csv")
print(res.round(4).to_string())
print(json.loads((RES / "shap.json").read_text()))
