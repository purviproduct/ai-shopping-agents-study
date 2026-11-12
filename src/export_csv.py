"""Export an AIBO results workbook to a plain CSV and a readable prompt file.

AIBO (github.com/wharton-generative-ai-labs/AIBO) writes each run to an .xlsx file. This script reads that file
and writes two things next to each other:

    <name>.csv          one row per run: condition, label, run, model, temperature, date,
                        response_1 ... response_k (each assistant turn), rating (the grader's number)
    <name>_prompts.md   condition 1 in full, then what each other condition changes, then every condition in full

Usage:
    python src/export_csv.py RESULTS.xlsx --out-dir DIR [--label 1="Control" --label 2="..."]
"""
import argparse
import csv
import difflib
import re
from pathlib import Path

import openpyxl


def rows_of(ws):
    return [list(r) for r in ws.iter_rows(values_only=True)]


def settings(wb):
    """{'Date': ..., 'Model for Rating': ..., ...} from the Settings sheet."""
    return {str(r[0]): r[1] for r in rows_of(wb["Settings"]) if r and r[0] is not None}


def conditions(wb):
    """[{system, rubric, prompts: [...], model, temperature}] in column order, from the Experiments sheet."""
    rows = {str(r[0]): r[1:] for r in rows_of(wb["Experiments"]) if r and r[0] is not None}
    n = sum(1 for c in rows["type"] if c is not None)
    turns = sorted((k for k in rows if re.fullmatch(r"Prompt \d+", k)), key=lambda k: int(k.split()[1]))
    out = []
    for i in range(n):
        out.append({
            "system": rows.get("System Message", [None] * n)[i],
            "rubric": rows.get("Evaluation Rubric", [None] * n)[i],
            "prompts": [rows[k][i] for k in turns if rows[k][i] not in (None, "")],
            "model": rows.get("Model", [None] * n)[i],
            "temperature": rows.get("Temperature", [None] * n)[i],
        })
    return out


def transcripts(wb):
    """[(condition, run, [assistant turns], rating, rating_raw)] from the Transcripts sheet.

    Each column is one run. Below the two header rows, rows alternate user turn / assistant turn, and the last
    filled row is the grader's 'Rating: x [verbatim rating: ...]' line.
    """
    rows = rows_of(wb["Transcripts"])
    exp_row = next(r for r in rows if r[0] == "Experiment #")
    it_row = next(r for r in rows if r[0] == "Iteration #")
    body = rows[rows.index(it_row) + 1:]
    out = []
    for col in range(1, len(exp_row)):
        if exp_row[col] is None:
            continue
        cells = [r[col] for r in body if col < len(r) and r[col] is not None]
        rating_cell = next((c for c in reversed(cells) if str(c).startswith("Rating:")), None)
        turns = [c for c in cells if c is not rating_cell]
        assistant = [str(t) for t in turns[1::2]]
        m = re.match(r"Rating:\s*([-\d.]+)", str(rating_cell or ""))
        rating = float(m.group(1)) if m else None
        out.append((int(str(exp_row[col]).split()[-1]), int(str(it_row[col]).split()[-1]), assistant, rating,
                    str(rating_cell or "")))
    return out


def fence(text):
    return "```text\n" + str(text).strip("\n") + "\n```"


def prompt_markdown(name, conds, labels, meta, first_note="control"):
    def lab(i):
        return labels.get(i + 1, f"Condition {i + 1}")

    def full(c):
        parts = []
        if c["system"]:
            parts.append("System message:\n\n" + fence(c["system"]))
        for k, p in enumerate(c["prompts"], 1):
            head = "Prompt" if len(c["prompts"]) == 1 else f"Turn {k} (user)"
            parts.append(f"{head}:\n\n" + fence(p))
        return "\n\n".join(parts)

    def flat(c):
        lines = []
        if c["system"]:
            lines += ["[system]"] + str(c["system"]).splitlines()
        for k, p in enumerate(c["prompts"], 1):
            lines += [f"[turn {k}]"] + str(p).splitlines()
        return lines

    md = [f"# Prompts: {name}", "",
          f"Generated from the AIBO results workbook by `src/export_csv.py`. Model {conds[0]['model']} at "
          f"temperature {conds[0]['temperature']}. Grader {meta.get('Model for Rating')} at temperature "
          f"{meta.get('Temperature for Rating')}. Run date {meta.get('Date')}.", ""]
    first = f"## 1. {lab(0)}" + (f" ({first_note})" if first_note else "")
    md += [first, "", full(conds[0]), ""]
    for i, c in enumerate(conds[1:], 1):
        diff = list(difflib.unified_diff(flat(conds[0]), flat(c), lineterm="", n=1))[2:]
        diff = [d for d in diff if not d.startswith("@@")]
        md += [f"## {i + 1}. {lab(i)}: what changes from condition 1", "",
               "```diff\n" + "\n".join(diff) + "\n```" if diff else "No change in the prompt text.", ""]
    rubrics = {c["rubric"] for c in conds}
    if len(rubrics) == 1:
        md += ["## Grader prompt (same for every condition)", "", fence(conds[0]["rubric"]), ""]
    md += ["## Every condition in full", ""]
    for i, c in enumerate(conds):
        md += [f"<details><summary>{i + 1}. {lab(i)}</summary>", "", full(c), ""]
        if len(rubrics) > 1:
            md += ["Grader prompt:", "", fence(c["rubric"]), ""]
        md += ["</details>", ""]
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--name", help="output file stem (default: workbook name without '-analysis_results')")
    ap.add_argument("--label", action="append", default=[], help='e.g. --label 1="Control"')
    ap.add_argument("--first-note", default="control",
                    help='note after condition 1\'s heading (default "control"; "" for none)')
    a = ap.parse_args()

    labels = {int(k): v for k, v in (s.split("=", 1) for s in a.label)}
    name = a.name or a.results.stem.replace("-analysis_results", "")
    wb = openpyxl.load_workbook(a.results, read_only=True, data_only=True)
    meta, conds, runs = settings(wb), conditions(wb), transcripts(wb)
    a.out_dir.mkdir(parents=True, exist_ok=True)

    k = max(len(r[2]) for r in runs)
    with open(a.out_dir / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["condition", "label", "run", "model", "temperature", "date"]
                   + [f"response_{i}" for i in range(1, k + 1)] + ["rating", "rating_raw"])
        for cond, run, turns, rating, raw in runs:
            c = conds[cond - 1]
            w.writerow([cond, labels.get(cond, ""), run, c["model"], c["temperature"], meta.get("Date")]
                       + turns + [""] * (k - len(turns)) + [rating, raw])
    (a.out_dir / f"{name}_prompts.md").write_text(prompt_markdown(name, conds, labels, meta, a.first_note),
                                                       encoding="utf-8")
    print(f"{name}: {len(runs)} runs, {len(conds)} conditions -> {a.out_dir}")


if __name__ == "__main__":
    main()
