"""Read both pilot result workbooks and report the pre-registered numbers.

    python src/analyze_pilots.py
"""

import random
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"


def runs(path):
    """{experiment number: [(rating, response), ...]} from the Transcripts sheet."""
    ws = openpyxl.load_workbook(path, data_only=True)["Transcripts"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    exp_row = next(r for r in rows if r[0] == "Experiment #")
    # Match the rating row by content, not by its column-A label (Breakage 5).
    rating_idx = next(i for i, r in enumerate(rows) if any(str(c).startswith("Rating:") for c in r if c))
    rating_row, response_row = rows[rating_idx], rows[rating_idx - 1]
    out = defaultdict(list)
    for col in range(1, len(exp_row)):
        if exp_row[col] is None:
            continue
        n = int(str(exp_row[col]).split()[-1])
        m = re.match(r"Rating:\s*([-\d.]+|None|nan)", str(rating_row[col]))
        val = float(m.group(1)) if m and m.group(1) not in ("None", "nan") else None
        out[n].append((val, str(response_row[col])))
    return out


def first_line(text):
    return text.strip().splitlines()[0].strip()


# ---------------------------------------------------------------------------
# Test A: order flip
# ---------------------------------------------------------------------------
A = runs(OUT / "order_flip-analysis_results.xlsx")
A_NAMES = {1: "$1, Alder listed first", 2: "$1, Birch listed first",
           3: "$10, Alder listed first", 4: "$10, Birch listed first"}
print("=== TEST A: order flip (rating 1 = Alder first, theory: Alder at $1, Birch at $10)")
alder = {}
for n in sorted(A):
    vals = [v for v, _ in A[n]]
    nulls = sum(v is None for v in vals)
    alder[n] = sum(v == 1 for v in vals)
    print(f"  {n}. {A_NAMES[n]:26s} Alder first {alder[n]}/{len(vals)}   nulls {nulls}")
    # Grader check: the first line of every response should name the coded caterer.
    mismatch = [(v, first_line(r)) for v, r in A[n]
                if not ((v == 1 and first_line(r).lower().startswith("alder"))
                        or (v == 0 and first_line(r).lower().startswith("birch")))]
    if mismatch:
        print(f"     grader/first-line mismatches: {mismatch}")
a1, n1 = alder[1] + alder[2], len(A[1]) + len(A[2])
a10, n10 = alder[3] + alder[4], len(A[3]) + len(A[4])
_, p = fisher_exact([[a1, n1 - a1], [a10, n10 - a10]])
print(f"  pooled: Alder first {a1}/{n1} at $1 vs {a10}/{n10} at $10, difference "
      f"{100 * (a1 / n1 - a10 / n10):.0f} points, Fisher p = {p:.2g}")
order = 100 * ((alder[1] + alder[3]) / 20 - (alder[2] + alder[4]) / 20)
print(f"  order effect (Alder listed first minus Birch listed first): {order:+.0f} points")
for n in (1, 3):
    print(f"  sample explanation, version {n}: {A[n][0][1].strip()[:300]!r}")

# ---------------------------------------------------------------------------
# Test B: reads the why
# ---------------------------------------------------------------------------
B = runs(OUT / "reason_reading-analysis_results.xlsx")
B_NAMES = {1: "Plain", 2: "Doesn't apply (vegan)", 3: "Clean", 4: "Applies (never replied)"}
print("\n=== TEST B: reads the why (chance 0-100)")
vals = {}
for n in sorted(B):
    v = [x for x, _ in B[n]]
    nulls = sum(x is None for x in v)
    vals[n] = [x for x in v if x is not None]
    sd = st.stdev(vals[n]) if len(vals[n]) > 1 else 0
    print(f"  {n}. {B_NAMES[n]:24s} mean {st.mean(vals[n]):5.1f}  sd {sd:4.1f}  "
          f"values {sorted(vals[n])}  nulls {nulls}")
    # Grader check: the first line of the response should be the extracted number.
    for x, r in B[n]:
        nums = re.findall(r"\d+(?:\.\d+)?", first_line(r))
        if not nums or abs(float(nums[0]) - (x or -1)) > 0.5:
            print(f"     grader/first-line mismatch: rating {x}, first line {first_line(r)!r}")


def index(plain, nonapp, clean):
    return (st.mean(nonapp) - st.mean(plain)) / (st.mean(clean) - st.mean(plain))


gap = st.mean(vals[3]) - st.mean(vals[1])
rui = index(vals[1], vals[2], vals[3])
rng = random.Random(0)
boot = []
for _ in range(5000):
    s = [rng.choices(vals[k], k=len(vals[k])) for k in (1, 2, 3)]
    if st.mean(s[2]) - st.mean(s[0]) > 0:
        boot.append(index(*s))
boot.sort()
lo, hi = boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot)) - 1]
print(f"  gate 1, Clean - Plain = {gap:.1f} (needs >= 10)")
print(f"  gate 2, Applies < Plain: {st.mean(vals[4]):.1f} vs {st.mean(vals[1]):.1f}")
print(f"  reason-use index = {rui:.2f}  (95% bootstrap {lo:.2f} to {hi:.2f})")
for n in (2, 4):
    print(f"  explanations, version {n} ({B_NAMES[n]}):")
    for x, r in B[n]:
        body = " ".join(r.strip().splitlines()[1:]).strip()
        print(f"    [{x:g}] {body[:220]}")
