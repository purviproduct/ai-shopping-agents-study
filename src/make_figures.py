"""Draw the two README figures from the saved results. No model calls.

    python src/make_figures.py

figures/1_says_vs_counts.png      the 300 runs on the record with the reason, by what the reply did
figures/2_good_sellers_lost.png   good sellers lost in the paper's example, by how shoppers read the record
                                  (numbers parsed from results/reader_sim_output.txt)
"""
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from aibo_results import NOTICED, runs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#a3a29c"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 11, "axes.edgecolor": GRID, "text.color": INK,
                     "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK})


def bars(ax, labels, values, colors, fmt, xmax):
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=colors, height=0.56, edgecolor=SURFACE, linewidth=2)
    for yi, v in zip(y, values):
        ax.text(v + xmax * 0.012, yi, fmt(v), va="center", ha="left", color=INK, fontsize=11)
    ax.set_yticks(list(y), labels)
    ax.set_xlim(0, xmax)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_facecolor(SURFACE)


def header(fig, title, subtitle):
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.text(0.015, 0.95, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.885, subtitle, fontsize=10, color=INK_2, va="top")


def legend(ax, items):
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in items]
    ax.legend(handles, [t for t, _ in items], loc="lower right", frameon=False, fontsize=10)


# Figure 1: what the 300 replies did with the reason
reasoned = runs(ROOT / "data/reason_reading_300-analysis_results.xlsx")[2]
counted = [(x, t) for x, t in reasoned if 65 <= x <= 69]
groups = [
    ("Wrote that the failures don't apply,\nthen answered 67% (4 of 6)", sum(bool(NOTICED.search(t)) for _, t in counted), ORANGE),
    ("Answered 67% without saying so", sum(not NOTICED.search(t) for _, t in counted), ORANGE),
    ("Answered 80% to 90%", sum(80 <= x <= 90 for x, _ in reasoned), BLUE),
    ("Answered 100%", sum(x == 100 for x, _ in reasoned), BLUE),
]
assert sum(g[1] for g in groups) == len(reasoned) == 300, "every run must fall in one group"
fig, ax = plt.subplots(figsize=(9, 3.9), facecolor=SURFACE)
bars(ax, [g[0] for g in groups], [g[1] for g in groups], [g[2] for g in groups], lambda v: f"{v}", 200)
ax.set_xlabel("Runs (of 300)")
legend(ax, [("Counted the failures", ORANGE), ("Used the reason", BLUE)])
header(fig, "gpt-5-mini read the reason, then counted the failure anyway",
       "Record: 4 passes, 2 failures marked \"no vegan menu\". The client needs no vegan menu. 300 runs, temperature 1.")
fig.savefig(OUT / "1_says_vs_counts.png", dpi=200, facecolor=SURFACE)

# Figure 2: good sellers lost in the paper's example, from the simulation output
text = (ROOT / "results/reader_sim_output.txt").read_text(encoding="utf-8")
block = text.strip().split("\n=== ")[0]  # the paper's own example; later blocks are robustness checks
assert block.startswith("=== Paper's Prop 6.5 example"), "unexpected simulation output layout"


def lost(row_label):
    m = re.search(re.escape(row_label) + r"\s+([\d.]+)", block)
    return 100 * float(m.group(1))


rows = [
    ("Shallow search (the paper's baseline)", "Shallow search, the paper's market M", GRAY),
    ("Deep search, record says only \"Failed\"", "Deep, niche failures counted as plain (alpha 0)", GRAY),
    ("Reason recorded, every shopper reads\nlike gpt-5-mini's average answer", "gpt-5-mini number first, average reader (alpha 0.17)", BLUE),
    ("Reason recorded, every shopper is\ngpt-5-mini at temperature 0", "gpt-5-mini at temp 0, every agent counts (alpha 0)", BLUE),
    ("Reason recorded, each shopper is a\nfresh gpt-5-mini answer (temperature 1)", "gpt-5-mini number first, sampled readers", BLUE),
    ("Reason recorded, gpt-5.6-luna shoppers", "gpt-5.6-luna (alpha 1)", BLUE),
    ("Reason recorded, the paper's ideal reader", "Paper's Bayesian transcript reader", GRAY),
]
fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=SURFACE)
bars(ax, [r[0] for r in rows], [lost(r[1]) for r in rows], [r[2] for r in rows], lambda v: f"{v:.0f}%", 60)
ax.set_xlabel("Good sellers lost (%)")
legend(ax, [("Paper's benchmarks", GRAY), ("AI shoppers from the experiment", BLUE)])
header(fig, "Recording the reason helps only if some shoppers use it",
       "Simulation of the paper's Prop 6.5 example: 20,000 runs of one good seller, 500 shoppers each.")
fig.savefig(OUT / "2_good_sellers_lost.png", dpi=200, facecolor=SURFACE)
print("wrote", *sorted(p.name for p in OUT.glob("*.png")))
