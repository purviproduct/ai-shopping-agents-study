"""A one-shopper-at-a-time market where every shopper is a live gpt-5-mini call.

    AIBO_DIR=/path/to/AIBO python src/llm_market.py
    AIBO_DIR=/path/to/AIBO python src/llm_market.py --caterers 1 --shoppers 8   # pilot

Model calls go through AIBO's call_llm (github.com/wharton-generative-ai-labs/AIBO), so AIBO_DIR must point to an
AIBO checkout. Put OPENAI_API_KEY in that checkout's .env file: AIBO's call_llm reads the key from there.

The paper's Prop 6.5 example with LLM readers instead of a formula. Every caterer is good: it can take any event,
but it has no vegan menu. Each shopper's client needs a vegan menu with probability 1/2 (the paper's niche screen).
Shoppers arrive one at a time. Each one's AI sees its own client's needs, the caterer's record so far, and the
economics (an inquiry costs $20, a successful booking is worth $100, so inquiring pays when the chance is above
20%, the paper's c = 1/5). It gives a chance and decides INQUIRE or SKIP. An inquiry passes for a client with no
dietary needs and fails for a vegan client; the result is added to the record before the next shopper arrives.

Two conditions on the same caterers and the same client sequences (paired):
    reasons      failures are recorded as "Failed (reason: no vegan menu)"
    no_reasons   failures are recorded as "Failed"

A caterer is counted as stalled if none of its last STALL_WINDOW shoppers inquired.
"""

import argparse
import asyncio
import json
import logging
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import os  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
AIBO_DIR = os.environ.get("AIBO_DIR")
if not AIBO_DIR or not (Path(AIBO_DIR) / "engine" / "call_llm.py").exists():
    sys.exit("Set AIBO_DIR to an AIBO checkout (github.com/wharton-generative-ai-labs/AIBO).")
sys.path.insert(0, str(Path(AIBO_DIR).resolve()))

from dotenv import load_dotenv  # noqa: E402

from engine.call_llm import call_llm  # noqa: E402

logger = logging.getLogger("llm_market")

MODEL = {"model": "gpt-5-mini", "temperature": 1}
P_VEGAN = 0.5
STALL_WINDOW = 10
NEEDS = {False: "none", True: "vegan menu required"}
FAIL_LINE = {"reasons": "Failed (reason: no vegan menu)", "no_reasons": "Failed"}

PROMPT = """You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: {needs}
- Budget: covers this caterer's listed price

A successful booking is worth $100 to your client. Sending an inquiry costs your client $20, and only an inquiry tells you whether Harbor Table can meet your client's requirements. If you skip, your client books no caterer.

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

{record}

Put the chance, from 0 to 100, that Harbor Table will meet your client's requirements alone on the first line. Put INQUIRE or SKIP alone on the second line. Then give one sentence explaining your choice."""

NUM = re.compile(r"\d+(?:\.\d+)?")


def show_record(lines: list[str]) -> str:
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start=1)) if lines else "No inquiries yet."


def parse(reply: str) -> tuple[float | None, str | None]:
    lines = [ln.strip().strip("*").strip() for ln in reply.strip().splitlines() if ln.strip()]
    chance = None
    if lines:
        nums = NUM.findall(lines[0])
        chance = float(nums[0]) if nums else None
    decision = next((w for ln in lines[1:3] for w in ("INQUIRE", "SKIP") if w in ln.upper()), None)
    return chance, decision


async def shopper(needs_vegan: bool, record: list[str]) -> dict:
    prompt = PROMPT.format(needs=NEEDS[needs_vegan], record=show_record(record))
    for attempt in range(3):
        reply, cost = await call_llm(prompt, MODEL, return_pricing=True)
        chance, decision = parse(reply)
        if decision is not None:
            return {"reply": reply, "chance": chance, "decision": decision, "cost": cost, "attempts": attempt + 1}
        logger.warning("Could not read a decision (attempt %d); asking again", attempt + 1)
    return {"reply": reply, "chance": chance, "decision": "SKIP", "cost": cost, "attempts": 3, "unparsed": True}


async def run_caterer(condition: str, idx: int, clients: list[bool]) -> dict:
    record: list[str] = []
    steps = []
    for t, vegan in enumerate(clients, start=1):
        s = await shopper(vegan, record)
        s.update({"shopper": t, "vegan_client": vegan, "record_before": list(record)})
        if s["decision"] == "INQUIRE":
            s["outcome"] = FAIL_LINE[condition] if vegan else "Passed"
            record.append(s["outcome"])
        steps.append(s)
    tail = steps[-STALL_WINDOW:]
    return {"condition": condition, "caterer": idx, "steps": steps, "record": record,
            "stalled": not any(s["decision"] == "INQUIRE" for s in tail),
            "passes": sum(s.get("outcome") == "Passed" for s in steps)}


def timeline(c: dict) -> str:
    """P passed, F failed, - skipped (client with no needs), v skipped (vegan client)."""
    out = []
    for s in c["steps"]:
        if s["decision"] == "INQUIRE":
            out.append("P" if s["outcome"] == "Passed" else "F")
        else:
            out.append("v" if s["vegan_client"] else "-")
    return " ".join(out)


async def main_async(args) -> None:
    rng = random.Random(args.seed)
    clients = [[rng.random() < P_VEGAN for _ in range(args.shoppers)] for _ in range(args.caterers)]
    if args.unlucky_start:
        # Prop 6.5's case: the first client needs a vegan menu, so the first inquiry on an empty record fails.
        for c in clients:
            c[0] = True
    started = time.monotonic()
    tasks = [run_caterer(cond, k, clients[k]) for cond in ("reasons", "no_reasons") for k in range(args.caterers)]
    results = await asyncio.gather(*tasks)

    for cond in ("reasons", "no_reasons"):
        rows = [r for r in results if r["condition"] == cond]
        logger.info("\n=== %s (%s): P passed, F failed, - skipped, v skipped by a vegan client", cond, FAIL_LINE[cond])
        for r in rows:
            logger.info("  caterer %2d  %s   %s", r["caterer"] + 1, timeline(r), "STALLED" if r["stalled"] else "kept")
        logger.info("  stalled: %d of %d", sum(r["stalled"] for r in rows), len(rows))

    calls = sum(len(r["steps"]) + sum(s["attempts"] - 1 for s in r["steps"]) for r in results)
    cost = sum(s["cost"] or 0 for r in results for s in r["steps"])
    unparsed = sum(bool(s.get("unparsed")) for r in results for s in r["steps"])
    run_at = datetime.now(timezone.utc)
    out = REPO / "data" / f"llm_market_results_{run_at:%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps({"run_at": run_at.isoformat(), "model": MODEL, "args": vars(args),
                               "p_vegan": P_VEGAN, "stall_window": STALL_WINDOW, "results": results},
                              indent=1, ensure_ascii=False), encoding="utf-8")
    logger.info("\n%d calls, $%.3f, %d unparsed, %.0fs. Results: %s", calls, cost, unparsed,
                time.monotonic() - started, out.relative_to(REPO))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--caterers", type=int, default=10, help="caterers per condition")
    ap.add_argument("--shoppers", type=int, default=20, help="shoppers per caterer, one at a time")
    ap.add_argument("--seed", type=int, default=0, help="seed for the clients' dietary needs (shared by both conditions)")
    ap.add_argument("--no-unlucky-start", dest="unlucky_start", action="store_false",
                    help="let the first client's needs be random instead of vegan")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "LiteLLM", "litellm", "engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    load_dotenv(REPO / ".env")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
