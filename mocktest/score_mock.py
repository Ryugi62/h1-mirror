"""Score the blind transcription of the mock register rows against ground truth.
Usage: python3 score_mock.py truth.json predictions.jsonl results.json
Field match = equal after lower-casing and removing spaces/punctuation. Verdict = engine category of the predicted drug
line equals the category of the true line (brand table + WHO rule table), i.e. what the mirror would count."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "engine")
sys.path.insert(0, ENGINE)
from domain.aware import BrandTable, RuleTable  # noqa: E402

FIELDS = ["date", "prescriber_name", "reg_no", "drug_line", "qty"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def rule_table():
    aw = json.load(open(os.path.join(ENGINE, "data", "aware2023.json")))
    nr = json.load(open(os.path.join(ENGINE, "data", "notrec2023.json")))["combinations"]
    br = BrandTable(json.load(open(os.path.join(ENGINE, "data", "brandmap-gautham2022.json")))["brands"])
    return RuleTable(aw, nr, br)


def score(truth, preds):
    rt = rule_table()
    p = {r["id"]: r for r in preds}
    rows, hits = [], {f: 0 for f in FIELDS + ["verdict", "strength", "reg_digits"]}
    for t in truth:
        q = p.get(t["id"], {})
        r = {"id": t["id"], "font": t["font"]}
        for f in FIELDS:
            r[f] = norm(q.get(f)) == norm(t[f])
            hits[f] += r[f]
        tv, pv = rt.classify_label(t["drug_line"]), rt.classify_label(q.get("drug_line") or "")
        r["verdict"] = tv == pv
        r["strength"] = re.findall(r"\d+", t["drug_line"]) == re.findall(r"\d+", q.get("drug_line") or "")
        r["reg_digits"] = re.sub(r"\D", "", t["reg_no"]) == re.sub(r"\D", "", q.get("reg_no") or "")
        hits["reg_digits"] += r["reg_digits"]
        hits["verdict"] += r["verdict"]
        hits["strength"] += r["strength"]
        r["true_verdict"], r["pred_verdict"] = tv, pv
        rows.append(r)
    n = len(truth)
    by_font = {}
    for r in rows:
        by_font.setdefault(r["font"], []).append(r["verdict"])
    return {"n": n, "correct": hits, "pct": {k: round(100 * v / n, 1) for k, v in hits.items()},
            "all_fields_correct": sum(all(r[f] for f in FIELDS) for r in rows),
            "verdict_by_font": {k: f"{sum(v)}/{len(v)}" for k, v in by_font.items()}, "rows": rows}


if __name__ == "__main__":
    truth = json.load(open(sys.argv[1]))
    preds = [json.loads(l) for l in open(sys.argv[2]) if l.strip().startswith("{")]
    res = score(truth, preds)
    json.dump(res, open(sys.argv[3], "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
