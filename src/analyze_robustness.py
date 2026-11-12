"""Read the robustness result workbooks and report the pre-registered numbers.

    python src/analyze_robustness.py
"""

import math
import random
import re
import statistics as st
import sys
from pathlib import Path

from scipy.stats import fisher_exact, ttest_ind

sys.path.insert(0, str(Path(__file__).parent))
from aibo_results import runs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"

from aibo_results import NOTICED  # noqa: E402  (phrases that show a reply noticed the reason doesn't apply)


def lines(text):
    return [ln.strip() for ln in text.strip().splitlines() if ln.strip()]


def check_lines(col, which):
    """The extracted rating should match the number on the first (or last) line."""
    bad = []
    for x, r in col:
        ls = lines(r)
        ln = ls[0] if which == "first" else ls[-1]
        nums = re.findall(r"\d+(?:\.\d+)?", ln)
        if x is None or not nums or abs(float(nums[0 if which == "first" else -1]) - x) > 0.5:
            bad.append((x, ln[:80]))
    return bad


def logit(p):
    p = min(max(p / 100, 0.005), 0.995)
    return math.log(p / (1 - p))


def boot_index(plain, da, clean, n=5000, seed=0):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        p, d, c = (rng.choices(v, k=len(v)) for v in (plain, da, clean))
        if st.mean(c) - st.mean(p) > 0:
            out.append((st.mean(d) - st.mean(p)) / (st.mean(c) - st.mean(p)))
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]


def describe(name, v):
    sd = st.stdev(v) if len(v) > 1 else 0
    return f"  {name:28s} n={len(v):2d} mean {st.mean(v):5.1f} sd {sd:4.1f} values {sorted(v)}"


def test_b(path, names, which="first"):
    data = runs(path)
    print(f"\n=== {path.name}")
    vals = {}
    for n in sorted(data):
        col = data[n]
        nulls = sum(x is None for x, _ in col)
        vals[n] = [x for x, _ in col if x is not None]
        print(describe(f"{n}. {names[n]}", vals[n]) + (f" nulls {nulls}" if nulls else ""))
        bad = check_lines(col, which)
        if bad:
            print(f"     {which}-line mismatches: {bad}")
    plain, da, clean = vals[1], vals[2], vals[3]
    gap = st.mean(clean) - st.mean(plain)
    idx = (st.mean(da) - st.mean(plain)) / gap
    lo, hi = boot_index(plain, da, clean)
    lg = [st.mean([logit(x) for x in v]) for v in (plain, da, clean)]
    print(f"  gate 1: Clean - Plain = {gap:.1f}")
    print(f"  forgive index = {idx:.2f} (95% bootstrap {lo:.2f} to {hi:.2f}); log-odds version {(lg[1] - lg[0]) / (lg[2] - lg[0]):.2f}")
    print(f"  Doesn't apply vs Plain: Welch p = {ttest_ind(da, plain, equal_var=False).pvalue:.2g}")
    mode = st.mode(plain)
    counted = [(x, r) for x, r in data[2] if x is not None and abs(x - mode) <= 2]
    read = [x for x in da if x >= st.mean(clean) - 5]
    noticed = sum(bool(NOTICED.search(r)) for _, r in counted)
    print(f"  split of 'Doesn't apply' runs: counted (within 2 of Plain's mode {mode:g}) {len(counted)}/{len(da)}, "
          f"read (>= Clean - 5) {len(read)}/{len(da)}, other {len(da) - len(counted) - len(read)}")
    print(f"  counted runs whose text says the failures don't apply: {noticed}/{len(counted)}")
    for x, r in counted[:2]:
        print(f"    e.g. [{x:g}] {' '.join(lines(r))[:230]}")
    res = {"index": idx, "lo": lo, "hi": hi, "h": len(read) / len(da), "counted": len(counted) / len(da)}
    if 4 in vals:
        print(f"  gate 2: Applies (never replied) {st.mean(vals[4]):.1f} vs Plain {st.mean(plain):.1f}, "
              f"Welch p = {ttest_ind(vals[4], plain, equal_var=False).pvalue:.2g}")
    if 6 in vals:
        pv, rv = vals[5], vals[6]
        punish = (st.mean(pv) - st.mean(rv)) / st.mean(pv)
        print(f"  vegan client: Plain {st.mean(pv):.1f} -> 'no vegan menu' {st.mean(rv):.1f}; "
              f"punish index {punish:.2f} (1 = all the way to 0); Welch p = {ttest_ind(rv, pv, equal_var=False).pvalue:.2g}")
        print(f"  asymmetry (punish - forgive) = {punish - idx:+.2f}")
        res["punish"] = punish
    return res


NAMES_V2 = {1: "Plain", 2: "Doesn't apply (vegan)", 3: "Clean", 4: "Applies (never replied)",
            5: "Plain, vegan client", 6: "No vegan menu, vegan client"}
NAMES_RF = {1: "Plain (reason first)", 2: "Doesn't apply (reason first)", 3: "Clean (reason first)"}

results = {}
for tag, suffix in (("gpt-5-mini", ""), ("gpt-5.6-luna", "_luna")):
    results[tag] = {
        "number_first": test_b(OUT / f"reason_reading_v2{suffix}-analysis_results.xlsx", NAMES_V2),
        "reason_first": test_b(OUT / f"reason_first{suffix}-analysis_results.xlsx", NAMES_RF, which="last"),
    }

print("\n=== SUMMARY: forgive index (0 = counts the failure, 1 = ignores it as it should)")
for tag, r in results.items():
    nf, rf = r["number_first"], r["reason_first"]
    print(f"  {tag:13s} number first {nf['index']:.2f} [{nf['lo']:.2f}, {nf['hi']:.2f}] read-share {nf['h']:.2f} | "
          f"reason first {rf['index']:.2f} [{rf['lo']:.2f}, {rf['hi']:.2f}] read-share {rf['h']:.2f} | "
          f"punish {nf['punish']:.2f}")

# ---------------------------------------------------------------------------
# Test A on gpt-5.6-luna
# ---------------------------------------------------------------------------
A = runs(OUT / "order_flip_luna-analysis_results.xlsx")
A_NAMES = {1: "$1, Alder listed first", 2: "$1, Birch listed first",
           3: "$10, Alder listed first", 4: "$10, Birch listed first"}
print("\n=== order_flip_luna (1 = Alder first; theory: Alder at $1, Birch at $10)")
alder = {}
for n in sorted(A):
    v = [x for x, _ in A[n]]
    alder[n] = sum(x == 1 for x in v)
    mism = [(x, lines(r)[0][:40]) for x, r in A[n]
            if not ((x == 1 and lines(r)[0].lower().lstrip("*").startswith("alder"))
                    or (x == 0 and lines(r)[0].lower().lstrip("*").startswith("birch")))]
    print(f"  {n}. {A_NAMES[n]:26s} Alder first {alder[n]}/{len(v)}" + (f"  mismatches {mism}" if mism else ""))
a1, a10 = alder[1] + alder[2], alder[3] + alder[4]
print(f"  pooled: {a1}/20 at $1 vs {a10}/20 at $10, Fisher p = {fisher_exact([[a1, 20 - a1], [a10, 20 - a10]])[1]:.2g}; "
      f"order effect {100 * ((alder[1] + alder[3]) - (alder[2] + alder[4])) / 20:+.0f} points")
