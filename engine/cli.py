"""Run one month: python3 engine/cli.py examples/register-sample.csv --council examples/council-register-sample.txt --out out/
Writes one private HTML letter per registered prescriber (out/letters/<reg>.html), the district aggregate
(out/district.json) and a summary of lines the rule table could not classify (to map once)."""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adapters import register_csv  # noqa: E402
from adapters.letter_html import letter_html  # noqa: E402
from adapters.rule_files import from_dir  # noqa: E402
from application.monthly_mirror import run_month  # noqa: E402


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv")
    ap.add_argument("--month", default="2026-08")
    ap.add_argument("--out", default="out")
    ap.add_argument("--min-lines", type=int, default=20)
    ap.add_argument("--min-pharmacies", type=int, default=10)
    ap.add_argument("--council", help="text file, one registration number per line (letters only for listed numbers)")
    a = ap.parse_args(argv)

    rows = register_csv.parse(open(a.csv, encoding="utf-8").read())
    council = set(open(a.council, encoding="utf-8").read().split()) if a.council else None
    rep = run_month(rows, from_dir(os.path.join(HERE, "data")), a.month, a.min_lines, a.min_pharmacies, council)
    os.makedirs(os.path.join(a.out, "letters"), exist_ok=True)
    for reg, lt in rep.letters.items():
        page = f"<!doctype html><meta charset=utf-8><title>H1 Mirror {reg}</title><body style='margin:24px'>{letter_html(lt)}"
        open(os.path.join(a.out, "letters", f"{reg}.html"), "w", encoding="utf-8").write(page)
    summary = {"month": rep.month, "lines": rep.lines_total, "letters": len(rep.letters),
               "unregistered_lines": rep.unregistered_lines, "h1_photo_lines": rep.photo_lines,
               "unmatched_reg_lines": rep.unmatched_reg_lines, "unclassified_lines": rep.unclassified_lines,
               "unclassified_labels": rep.unclassified_labels, "district": rep.district}
    json.dump(summary, open(os.path.join(a.out, "district.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "unclassified_labels"}))
    return summary


if __name__ == "__main__":
    main()
