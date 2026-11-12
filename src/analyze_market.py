"""Summarize the live market run (llm_market.py) from data/llm_market_results.json.

    python src/analyze_market.py

Each caterer is good but has no vegan menu. Its first client is vegan, so its record opens with a failure. The same
client sequences run twice: failures recorded with the reason ("Failed (reason: no vegan menu)") and without it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
run = json.loads((ROOT / "data/llm_market_results.json").read_text(encoding="utf-8"))
BREAK_EVEN = 20  # an inquiry costs $20 and a booking is worth $100


def longest_skip_streak(steps):
    best = cur = 0
    for s in steps:
        cur = cur + 1 if s["decision"] == "SKIP" else 0
        best = max(best, cur)
    return best


print(f"Run at {run['run_at']}, model {run['model']}, {run['args']}")
rows = {}
for cond in ("reasons", "no_reasons"):
    cats = [r for r in run["results"] if r["condition"] == cond]
    steps = [s for r in cats for s in r["steps"]]
    second = [r["steps"][1] for r in cats if not r["steps"][1]["vegan_client"]]
    no_needs = [s for s in steps if s["shopper"] >= 2 and not s["vegan_client"]]
    vegan_with_fail = [s for s in steps if s["vegan_client"] and any(x.startswith("Failed") for x in s["record_before"])]
    rows[cond] = {
        "Caterers stuck (no inquiry in the last 10 shoppers)": f"{sum(r['stalled'] for r in cats)} of {len(cats)}",
        "Longest run of skips per caterer": " ".join(str(longest_skip_streak(r["steps"])) for r in cats),
        "Shopper 2 (no needs) after the opening failure: inquired": f"{sum(s['decision'] == 'INQUIRE' for s in second)}/{len(second)}",
        "Shopper 2: mean chance given": f"{sum(s['chance'] for s in second) / len(second):.0f}",
        "Clients with no needs who inquired (shoppers 2-20)": f"{sum(s['decision'] == 'INQUIRE' for s in no_needs)}/{len(no_needs)}",
        "Vegan clients who inquired with a failure on the record": f"{sum(s['decision'] == 'INQUIRE' for s in vegan_with_fail)}/{len(vegan_with_fail)}",
    }

print("\n| | with reasons | without reasons |\n|---|---|---|")
for k in rows["reasons"]:
    print(f"| {k} | {rows['reasons'][k]} | {rows['no_reasons'][k]} |")

steps = [s for r in run["results"] for s in r["steps"]]
match = sum((s["decision"] == "INQUIRE") == (s["chance"] is not None and s["chance"] > BREAK_EVEN) for s in steps)
print(f"\nCalls: {len(steps)} (retries {sum(s['attempts'] - 1 for s in steps)}), "
      f"unparsed {sum(bool(s.get('unparsed')) for s in steps)}, cost ${sum(s['cost'] or 0 for s in steps):.2f}")
print(f"Decisions that match 'inquire if the chance is above {BREAK_EVEN}%': {match} of {len(steps)}")

for r in run["results"]:
    if r["stalled"]:
        print(f"\nStuck caterer: {r['condition']}, caterer {r['caterer'] + 1}")
        for s in r["steps"][:6]:
            print(f"  shopper {s['shopper']:2d}  vegan={s['vegan_client']!s:5}  chance {s['chance']}  {s['decision']}")
