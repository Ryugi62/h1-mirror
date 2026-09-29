"""Accuracy audit of the rule table on real Indian products (v0.7).
sample-200.json: 200 marketed systemic antibiotic products drawn at random (seed 20260930) from the Indian catalogue scope.
reader-labels.json: labels written by an independent blind reader (a separate AI agent) who saw only the compositions and
the two WHO files, never the engine or its output. Usage: python3 audit/score_audit.py -> agreement + Wilson 95% CI."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
from adapters.rule_files import from_dir  # noqa: E402


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def main():
    rt = from_dir(os.path.join(HERE, "..", "engine", "data"))
    sample = json.load(open(os.path.join(HERE, "sample-200.json"), encoding="utf-8"))
    reader = {r["id"]: r["label"] for r in json.load(open(os.path.join(HERE, "reader-labels.json")))}
    rows = [(s["id"], s["composition"], rt.classify_label(s["bill_line"]), reader[s["id"]]) for s in sample]
    agree = sum(1 for _, _, e, r in rows if e == r)
    lo, hi = wilson(agree, len(rows))
    res = {"n": len(rows), "agree": agree, "agree_pct": round(100 * agree / len(rows), 1), "wilson95": [lo, hi],
           "disagreements": [{"id": i, "composition": c, "engine": e, "reader": r} for i, c, e, r in rows if e != r]}
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1, ensure_ascii=False)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k != "disagreements"}))
    for d in r["disagreements"]:
        print(d)
