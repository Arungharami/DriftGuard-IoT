import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
fig, ax = plt.subplots(figsize=(12, 5.2), dpi=200)
ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")

def box(x, y, w, h, text, fc, ec="#34495e", fs=9.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)

def arrow(a, b, text="", color="#2c3e50", rad=0.0, ls="-", toff=(0, 0.12)):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, lw=1.4, color=color,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))
    if text:
        ax.text((a[0] + b[0]) / 2 + toff[0], (a[1] + b[1]) / 2 + toff[1], text, ha="center",
                fontsize=8, color=color, style="italic")

# tiers
for x, w, t in [(0.1, 2.4, "Perception tier"), (2.8, 1.9, "Network tier"), (5.0, 6.9, "Edge gateway tier (DriftGuard)")]:
    ax.add_patch(FancyBboxPatch((x, 0.15), w, 4.85, boxstyle="round,pad=0.02", fc="#f7f9fa", ec="#bdc3c7", lw=0.8, ls="--"))
    ax.text(x + w / 2, 4.78, t, ha="center", fontsize=10, fontweight="bold", color="#566573")

for i, y in enumerate([3.55, 2.45, 1.35]):
    box(0.35, y, 1.9, 0.75, f"ESP32 node {i + 1}\nDHT22 + battery ADC", "#d6eaf8", fs=8.5)
box(3.0, 2.2, 1.5, 1.1, "MQTT broker\n(TCP/1883)", "#fdebd0")
for y in [3.9, 2.8, 1.7]:
    arrow((2.25, y), (3.0, 2.75), rad=0.0)

box(5.25, 2.2, 1.55, 1.1, "Flow feature\nextraction\n(log + one-hot)", "#e8f8f5", fs=8.5)
box(7.1, 2.2, 1.6, 1.1, "Tree / LightGBM\nclassifier\n(frozen fit)", "#d5f5e3", fs=8.5, bold=True)
box(9.05, 2.2, 1.6, 1.1, "Alert / dashboard\n(predicted class)", "#fadbd8", fs=8.5)
arrow((4.5, 2.75), (5.25, 2.75), "flows")
arrow((6.8, 2.75), (7.1, 2.75))
arrow((8.7, 2.75), (9.05, 2.75))

box(9.05, 0.45, 2.6, 1.0, "Delayed labels\n(analyst / ground truth,\nreleased after Δ = 5 ticks)", "#fcf3cf", fs=8.2)
box(5.25, 0.45, 3.45, 1.0, "ADWIN monitor on released errors\n(δ = 0.002, each error seen once)", "#ebdef0", fs=8.5)
arrow((9.05, 0.95), (8.7, 0.95), "errors")
box(5.25, 3.65, 3.45, 0.95, "Windowed refit: clone pipeline,\nfit on last W = 1000 released rows", "#d6eaf8", fs=8.5)
ax.plot([5.4, 5.4, 5.12, 5.12], [1.45, 1.75, 1.75, 4.1], color="#7d3c98", lw=1.4, ls="--")
arrow((5.1, 4.1), (5.26, 4.1), color="#7d3c98")
ax.text(5.15, 1.85, "alarm", fontsize=8, color="#7d3c98", style="italic", rotation=90, va="bottom")
arrow((7.9, 2.2), (7.9, 1.45), "", color="#2c3e50")
ax.text(7.97, 1.75, "predictions", fontsize=8, color="#2c3e50", style="italic")
arrow((7.9, 3.65), (7.9, 3.3), "new model", color="#1f5fa8", toff=(0.55, -0.1))
fig.tight_layout(); fig.savefig(OUT / "fig_architecture.png"); plt.close(fig)
