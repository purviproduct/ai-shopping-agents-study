"""How many of the 300 "doesn't apply" runs wrote that the failures don't apply, then answered the plain 4-of-6 rate?

    python src/count_says_doesnt_apply.py

A run "counts the failures" if it answered 65 to 69 (4 of 6 is 67%), the same rule as analyze_300.py. A run "says
they don't apply" if its one-sentence explanation matches NOTICED in aibo_results.py, the phrase list used by
analyze_robustness.py.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aibo_results import NOTICED, runs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
data = runs(ROOT / "data/reason_reading_300-analysis_results.xlsx")
plain, reasoned = data[1], data[2]

counted = [(x, t) for x, t in reasoned if x is not None and 65 <= x <= 69]
says = [(x, t) for x, t in counted if NOTICED.search(t)]
print(f"Plain record: {len(plain)} runs, answers {dict(Counter(x for x, _ in plain))}")
print(f"Record with the reason: {len(reasoned)} runs")
print(f"  answered the plain 4-of-6 rate (65-69): {len(counted)}")
print(f"  of those, wrote that the failures don't apply: {len(says)}")
print(f"  => {len(says)} of {len(reasoned)} runs said the failures don't apply and still counted them")
print(f"  answered 80 or more: {sum(1 for x, _ in reasoned if x is not None and x >= 80)}")
