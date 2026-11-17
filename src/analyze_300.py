"""The 300-shopper version of "reads the why": spread of answers, and the simulation rerun on all 300.

    python src/analyze_300.py
"""

import math
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aibo_results import runs  # noqa: E402
from reader_sim import llr_table, simulate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PLAIN, CLEAN = 67.0, 92.4  # Plain is 4 of 6; Clean is the 30-run mean from reason_reading_v2 (2026-11-02)


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


data = runs(ROOT / "data/reason_reading_300-analysis_results.xlsx")
names = {1: "Plain “Failed”", 2: "“Failed (reason: no vegan menu)”"}
vals = {}
for n, label in names.items():
    v = [x for x, _ in data[n] if x is not None]
    vals[n] = v
    counts = sorted(Counter(round(x) for x in v).items())
    print(f"\n{label}: n={len(v)} (nulls {len(data[n]) - len(v)}), mean {st.mean(v):.1f}, sd {st.stdev(v):.1f}")
    print("  answers: " + ", ".join(f"{a}×{c}" for a, c in counts))

da = vals[2]
counted = sum(abs(x - PLAIN) <= 2 for x in da)
used = sum(x >= 80 for x in da)
lo, hi = wilson(used, len(da))
print(f"\nWith the reason: counted (answered 65-69) {counted}/{len(da)}, used it (80 or more) {used}/{len(da)} "
      f"= {100 * used / len(da):.1f}% (95% {100 * lo:.1f}-{100 * hi:.1f}%), other {len(da) - counted - used}")
print(f"Forgive index on the 300: {(st.mean(da) - PLAIN) / (CLEAN - PLAIN):.2f} (30-run value 0.17)")

# Simulation: the paper's Prop 6.5 example, readers drawn from these 300 answers.
eps = 0.01
alphas = [min(max((x - PLAIN) / (CLEAN - PLAIN), 0.0), 1.0) for x in da]
mix = Counter(round(a, 3) for a in alphas)
readers = [(llr_table(1 - eps, eps, 0.5, alpha=a), c / len(alphas)) for a, c in sorted(mix.items())]
lost, skipped = simulate(readers, 1 - eps, eps, 0.5, 0.2)
print(f"\nSimulation with readers drawn from the 300 answers: {100 * lost:.1f}% of good caterers lost, "
      f"{skipped:.1f} shoppers skip a live caterer on average (30-answer mix: 2.0%, 7.6)")
for drop in (1.0, 0.95, 0.9):
    sub = [(t, w) for (t, w), a in zip(readers, sorted(mix)) if a < drop]
    if len(sub) < len(readers):
        total = sum(w for _, w in sub)
        l2, _ = simulate([(t, w / total) for t, w in sub], 1 - eps, eps, 0.5, 0.2)
        print(f"  without answers at reason use >= {drop:.2f}: {100 * l2:.1f}% lost")
