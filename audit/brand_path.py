"""Brand-name path audit (v0.7): the same 200 products, written the way a bill reads (product name, e.g.
'Kefmax CV 50mg/31.25mg Syrup'), resolved through the national brand table, then classified.
(a) in-table: the full national table (production setting: every catalogue brand is known);
(b) held-out: table rebuilt WITHOUT the 200 sampled products (a brand the table has never seen).
Truth = the blind reader's labels (reader-labels.json). Needs the catalogue CSV (see run_india_catalogue.py).
Usage: python3 audit/brand_path.py <indian_medicine_data.csv>"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "engine")
sys.path.insert(0, ENGINE)
from adapters import india_catalogue  # noqa: E402
from application.catalogue_check import brand_table  # noqa: E402
from domain.aware import BrandTable, RuleTable  # noqa: E402
from score_audit import wilson  # noqa: E402


def run(csv_path):
    aw = json.load(open(os.path.join(ENGINE, "data", "aware2023.json")))
    nr = json.load(open(os.path.join(ENGINE, "data", "notrec2023.json")))["combinations"]
    gau = json.load(open(os.path.join(ENGINE, "data", "brandmap-gautham2022.json")))["brands"]
    sample = json.load(open(os.path.join(HERE, "sample-200.json"), encoding="utf-8"))
    truth = {r["id"]: r["label"] for r in json.load(open(os.path.join(HERE, "reader-labels.json")))}
    products = india_catalogue.parse(open(csv_path, encoding="utf-8").read())
    base = RuleTable(aw, nr)
    names = {s["product"] for s in sample}
    out = {}
    for mode, prods in (("in_table", products), ("held_out", [p for p in products if p.name not in names])):
        brands = brand_table(prods, base, india_catalogue.brand_of)
        brands.update(gau)
        rt = RuleTable(aw, nr, BrandTable(brands))
        got = [(s["id"], rt.classify_label(s["product"] + (" Injection" if "Injection" in s["bill_line"] else "")))
               for s in sample]
        resolved = [(i, v) for i, v in got if v != "Unclassified" or truth[i] == "Unclassified"]
        correct = sum(1 for i, v in got if v == truth[i])
        wrong = [(i, v, truth[i]) for i, v in resolved if v != truth[i]]
        out[mode] = {"n": len(got), "correct": correct, "wilson95": wilson(correct, len(got)),
                     "resolved": len(resolved), "correct_when_resolved": len(resolved) - len(wrong),
                     "wilson95_when_resolved": wilson(len(resolved) - len(wrong), len(resolved)) if resolved else None,
                     "wrong": wrong}
    json.dump(out, open(os.path.join(HERE, "brand-path-results.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), indent=1))
