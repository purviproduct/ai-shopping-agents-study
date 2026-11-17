"""Write data/csv/llm_market.csv (one row per shopper) from data/llm_market_results.json.

    python src/export_market_csv.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
run = json.loads((ROOT / "data/llm_market_results.json").read_text(encoding="utf-8"))
with open(ROOT / "data/csv/llm_market.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["condition", "caterer", "shopper", "vegan_client", "record_before", "chance", "decision", "outcome",
                "stalled_caterer", "reply"])
    for r in run["results"]:
        for s in r["steps"]:
            w.writerow([r["condition"], r["caterer"] + 1, s["shopper"], s["vegan_client"], " | ".join(s["record_before"]),
                        s["chance"], s["decision"], s.get("outcome", ""), r["stalled"], s["reply"]])
