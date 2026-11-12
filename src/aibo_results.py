"""Shared parser for AIBO result workbooks (the same parser as in analyze_pilots.py)."""

import re
from collections import defaultdict

import openpyxl


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


# Phrases that show the reply noticed the vegan failures don't bear on this client.
# Fix (2026-11-11): the apostrophe class now also matches the curly ’ that most replies use. The first version
# matched only the straight ' and undercounted (18 of 23 counted replies at N=30; 20 of 23 with this fix).
NOTICED = re.compile(r"irrelevant|not relevant|doesn['’]?t apply|does not apply|don['’]?t apply|do not apply|not apply"
                     r"|no dietary|not a concern|unaffected|not an issue|doesn['’]?t matter|does not matter"
                     r"|isn['’]?t relevant",
                     re.I)
