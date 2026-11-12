"""Build the two pilot workbooks from the anchoring template.

    python src/build_pilots.py
"""

import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "prompts/settings_template.xlsx"  # AIBO settings sheet (model, temperature, grader)
OUT_DIR = ROOT / "prompts"


def build(path, columns):
    """columns: list of (rubric, prompt). Settings are kept from the template."""
    wb = openpyxl.load_workbook(TEMPLATE)
    ws = wb["Experiments"]
    ws.delete_cols(2, ws.max_column)
    for i, (rubric, prompt) in enumerate(columns, start=2):
        ws.cell(1, i, f"Experiment {i - 1}")
        ws.cell(2, i, None)               # System Message
        ws.cell(3, i, rubric)             # Evaluation Rubric
        ws.cell(4, i, prompt)             # Prompt 1
        ws.cell(5, i, "[AI Responds]")    # Response 1
    wb.save(path)
    print(f"wrote {path} with {len(columns)} columns")


# ---------------------------------------------------------------------------
# Test A: the order flip
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
    (RUBRIC_A, PROMPT_A.format(cost=1, first=ALDER, second=BIRCH)),    # 1: $1, Alder listed first
    (RUBRIC_A, PROMPT_A.format(cost=1, first=BIRCH, second=ALDER)),    # 2: $1, Birch listed first
    (RUBRIC_A, PROMPT_A.format(cost=10, first=ALDER, second=BIRCH)),   # 3: $10, Alder listed first
    (RUBRIC_A, PROMPT_A.format(cost=10, first=BIRCH, second=ALDER)),   # 4: $10, Birch listed first
]

# ---------------------------------------------------------------------------
# Test B: does the agent read the why?
# ---------------------------------------------------------------------------

PROMPT_B = """You are an AI assistant booking a caterer for your client. Your client's event:
- Company dinner, Saturday evening, 80 guests
- Dietary needs: none
- Budget: covers this caterer's listed price

The booking platform shows this record for Harbor Table Catering. Each line is a recent inquiry made by another customer's AI assistant:

{record}

Before you contact them: what is the chance, from 0 to 100, that Harbor Table will meet your client's requirements? Put the number alone on the first line, then give one sentence explaining it."""

RUBRIC_B = """Below is someone's estimate of the chance, from 0 to 100, that a caterer will meet their client's requirements. Extract the number they gave. If they gave a range, use its midpoint. If they gave a probability between 0 and 1, multiply it by 100. Report only that number, in brackets, like [62].
Here is the response:
{response}"""


def record(fail_line):
    """Six inquiries with failures at lines 2 and 5, or four passes if fail_line is None."""
    if fail_line is None:
        lines = ["Passed"] * 4
    else:
        lines = ["Passed", fail_line, "Passed", "Passed", fail_line, "Passed"]
    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, start=1))


reason_reading = [
    (RUBRIC_B, PROMPT_B.format(record=record("Failed"))),                                             # 1: Plain
    (RUBRIC_B, PROMPT_B.format(record=record("Failed (reason: no vegan menu)"))),                      # 2: Doesn't apply
    (RUBRIC_B, PROMPT_B.format(record=record(None))),                                                  # 3: Clean
    (RUBRIC_B, PROMPT_B.format(record=record("Failed (reason: never replied to the inquiry)"))),       # 4: Applies
]

build(OUT_DIR / "order_flip.xlsx", order_flip)
build(OUT_DIR / "reason_reading.xlsx", reason_reading)
