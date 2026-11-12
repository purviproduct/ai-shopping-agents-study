"""Build the robustness workbooks for the "reads the why" result, plus the order flip on a second model.

    python src/build_robustness.py [luna]

Reuses the pilot prompts verbatim (build_pilots.py) so the gpt-5-mini columns 1-4 replicate the pilot at N=30.
"""

import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "prompts/settings_template.xlsx"  # AIBO settings sheet (model, temperature, grader)
OUT_DIR = ROOT / "prompts"

# Checked on models.litellm.ai. A second family was the goal, but the Anthropic and Google keys in .env
# are both rejected (401 / API_KEY_INVALID), so the second model is OpenAI's newest small tier instead.
SECOND_MODELS = {"luna": "gpt-5.6-luna", "gemini": "gemini/gemini-3.5-flash-lite", "haiku": "claude-haiku-5-5"}


def build(path, columns, model="gpt-5-mini", iterations=30):
    """columns: list of (rubric, prompt). Grader stays gpt-5-mini at temp 0 for every model."""
    wb = openpyxl.load_workbook(TEMPLATE)
    settings = wb["Settings"]
    for row in settings.iter_rows(min_row=2):
        if row[0].value == "Number of Iterations":
            row[1].value = iterations
        elif row[0].value == "Model for Response Generation":
            row[1].value = model
    ws = wb["Experiments"]
    ws.delete_cols(2, ws.max_column)
    for i, (rubric, prompt) in enumerate(columns, start=2):
        ws.cell(1, i, f"Experiment {i - 1}")
        ws.cell(2, i, None)               # System Message
        ws.cell(3, i, rubric)             # Evaluation Rubric
        ws.cell(4, i, prompt)             # Prompt 1
        ws.cell(5, i, "[AI Responds]")    # Response 1
    wb.save(path)
    print(f"wrote {path.name}: {len(columns)} columns x {iterations}, {model}")


# ---------------------------------------------------------------------------
# Test B v2: reads the why, with a client who does need vegan food
# ---------------------------------------------------------------------------

PROMPT_B = """You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: {needs}
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

{record}

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? {ask}"""

NUMBER_FIRST = "Put the number alone on the first line, then give one sentence explaining it."
REASON_FIRST = "First give one sentence explaining your reasoning, then put the number alone on the last line."

RUBRIC_B = """Below is someone's estimate of the chance, from 0 to 100, that a caterer will meet their client's requirements. Extract the number they gave. If they gave a range, use its midpoint. If they gave a probability between 0 and 1, multiply it by 100. Report only that number, in brackets, like [62].
Here is the response:
{response}"""

RUBRIC_B_LAST = """Below is someone's estimate of the chance, from 0 to 100, that a caterer will meet their client's requirements. Extract their final estimate, which should be the number on the last line. If they gave a range, use its midpoint. If they gave a probability between 0 and 1, multiply it by 100. Report only that number, in brackets, like [62].
Here is the response:
{response}"""

NONE, VEGAN = "none", "vegan menu required"
PLAIN, VEGAN_FAIL, NEVER = "Failed", "Failed (reason: no vegan menu)", "Failed (reason: never replied to the inquiry)"


def record(fail_line):
    """Six inquiries with failures at lines 2 and 5, or four passes if fail_line is None."""
    if fail_line is None:
        lines = ["Passed"] * 4
    else:
        lines = ["Passed", fail_line, "Passed", "Passed", fail_line, "Passed"]
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start=1))


def b(needs, fail_line, ask=NUMBER_FIRST, rubric=RUBRIC_B):
    return rubric, PROMPT_B.format(needs=needs, record=record(fail_line), ask=ask)


reason_v2 = [
    b(NONE, PLAIN),        # 1: Plain                     (baseline, same as pilot 1)
    b(NONE, VEGAN_FAIL),   # 2: Doesn't apply             (same as pilot 2)
    b(NONE, None),         # 3: Clean                     (same as pilot 3)
    b(NONE, NEVER),        # 4: Applies to anyone         (same as pilot 4)
    b(VEGAN, PLAIN),       # 5: Plain, vegan client       (new)
    b(VEGAN, VEGAN_FAIL),  # 6: Applies, decisive         (new: caterer has no vegan menu, client needs one)
]

reason_first = [
    b(NONE, PLAIN, REASON_FIRST, RUBRIC_B_LAST),       # 1: Plain
    b(NONE, VEGAN_FAIL, REASON_FIRST, RUBRIC_B_LAST),  # 2: Doesn't apply
    b(NONE, None, REASON_FIRST, RUBRIC_B_LAST),        # 3: Clean
]

# ---------------------------------------------------------------------------
# Test A on the second model (verbatim from build_pilots.py)
# ---------------------------------------------------------------------------

ALDER = "Alder: food is great 95% of the time. Price $40. Can take an event like this 20% of the time."
BIRCH = "Birch: food is great 70% of the time. Price $30. Can take an event like this 80% of the time."

PROMPT_A = """You are an AI assistant booking a caterer for your client's event. A successful event is worth $100 to your client. If the food turns out not to be great, the event is worth $0.

You don't know yet whether each caterer can take this event. To find out, you send an inquiry, which costs your client ${cost}. You contact caterers one at a time. If the caterer you contact can take the event, you book it right away, your client pays its price, and you stop. If it can't, you can then contact the other caterer.

{first}
{second}

Which caterer do you contact first? Put only the caterer's name on the first line, then give one sentence explaining your choice."""

RUBRIC_A = """Below is a response from an assistant deciding which caterer to contact first, Alder or Birch. Which caterer did it choose to contact first? Judge by the caterer named on the first line. If the first line names neither, use the caterer the explanation says to contact first. If Alder, output [1]. If Birch, output [0]. Report only that number in brackets.
Here is the response:
{response}"""

order_flip = [
    (RUBRIC_A, PROMPT_A.format(cost=1, first=ALDER, second=BIRCH)),
    (RUBRIC_A, PROMPT_A.format(cost=1, first=BIRCH, second=ALDER)),
    (RUBRIC_A, PROMPT_A.format(cost=10, first=ALDER, second=BIRCH)),
    (RUBRIC_A, PROMPT_A.format(cost=10, first=BIRCH, second=ALDER)),
]

if __name__ == "__main__":
    # argv[1]: "smoke-<tag>" for 3 single runs, or a tag from SECOND_MODELS (default "luna")
    arg = sys.argv[1] if len(sys.argv) > 1 else "luna"
    if arg.startswith("smoke-"):
        tag = arg[len("smoke-"):]
        build(OUT_DIR / f"smoke_{tag}.xlsx", reason_v2[4:] + reason_first[1:2], SECOND_MODELS[tag], iterations=1)
    else:
        model = SECOND_MODELS[arg]
        if arg == "luna":
            build(OUT_DIR / "reason_reading_v2.xlsx", reason_v2)
            build(OUT_DIR / "reason_first.xlsx", reason_first)
        build(OUT_DIR / f"reason_reading_v2_{arg}.xlsx", reason_v2, model)
        build(OUT_DIR / f"reason_first_{arg}.xlsx", reason_first, model)
        build(OUT_DIR / f"order_flip_{arg}.xlsx", order_flip, model, iterations=10)
