"""Reproduce the Round 1 evidence: python3 run_evidence.py EPD_202506 -> data/evidence-EPD_202506.json"""
import json
import os
import sys
import time
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from domain.aware import classify, shares, mirror  # noqa: E402
from adapters import epd  # noqa: E402

MIN_ITEMS = 100  # practices with fewer antibacterial items/month are excluded from the distribution (small-number noise)


def main(month: str) -> dict:
    aware = json.load(open(os.path.join(HERE, "data", "aware2023.json")))
    t0 = time.time()
    chem = epd.national_by_chemical(month)
    cat = {r["BNF_CHEMICAL_SUBSTANCE"]: classify(r["CHEMICAL_SUBSTANCE_BNF_DESCR"], aware) for r in chem}
    totals = {}
    for r in chem:
        totals[cat[r["BNF_CHEMICAL_SUBSTANCE"]]] = totals.get(cat[r["BNF_CHEMICAL_SUBSTANCE"]], 0) + r["items"]
    access = [c for c, v in cat.items() if v == "Access"]
    wr = [c for c, v in cat.items() if v in ("Watch", "Reserve")]
    orgs = epd.by_practice(month, access, wr)
    elapsed = round(time.time() - t0, 1)

    all_items = sum(totals.values())
    classified = all_items - totals.get("Unclassified", 0)
    prac = [dict(r, **shares(r["access_items"], r["wr_items"])) for r in orgs if r["total"] >= MIN_ITEMS]
    prac = [p for p in prac if p["access_share"] is not None]
    a_sorted = sorted(p["access_share"] for p in prac)
    w_sorted = sorted(p["wr_share"] for p in prac)
    cut = w_sorted[int(0.8 * (len(w_sorted) - 1))]
    top = [p for p in prac if p["wr_share"] >= cut]
    hist = {}
    for a in a_sorted:
        b = min(95, int(a * 100 // 5 * 5))
        hist[b] = hist.get(b, 0) + 1
    by_icb = {}
    for p in prac:
        by_icb.setdefault(p["ICB_CODE"], []).append(p["wr_share"])
    example = sorted(prac, key=lambda p: p["wr_share"])[int(0.95 * (len(prac) - 1))]
    ex_m = mirror(example["wr_share"], by_icb[example["ICB_CODE"]])

    out = {
        "month": month, "source": "NHSBSA English Prescribing Dataset (OGL v3.0), BNF 5.1 antibacterial drugs",
        "who_table": "WHO AWaRe classification 2023 (WHO-MHP-HPS-EML-2023.04, CC BY-NC-SA 3.0 IGO)",
        "elapsed_sec": elapsed,
        "items_total": all_items, "orgs_total": len(orgs), "chemicals": len(chem),
        "items_by_category": totals,
        "coverage_pct": round(100 * classified / all_items, 1),
        "access_pct_of_classified": round(100 * totals.get("Access", 0) / classified, 1),
        "watch_pct_of_classified": round(100 * totals.get("Watch", 0) / classified, 1),
        "reserve_pct_of_classified": round(100 * totals.get("Reserve", 0) / classified, 2),
        "practices_ge_min": len(prac), "min_items": MIN_ITEMS,
        "practice_access_share": {"min": round(100 * a_sorted[0], 1), "p10": round(100 * a_sorted[len(a_sorted) // 10], 1),
                                  "median": round(100 * median(a_sorted), 1), "p90": round(100 * a_sorted[9 * len(a_sorted) // 10], 1),
                                  "max": round(100 * a_sorted[-1], 1)},
        "practices_below_70pct_access": sum(1 for a in a_sorted if a < 0.70),
        "top20_wr": {"cutoff_pct": round(100 * cut, 1), "n": len(top),
                     "share_of_all_wr_items_pct": round(100 * sum(p["wr_items"] for p in top) / sum(p["wr_items"] for p in prac), 1)},
        "icb_access_range_pct": [round(100 * min(1 - median(v) for v in by_icb.values()), 1),
                                 round(100 * max(1 - median(v) for v in by_icb.values()), 1)],
        "histogram_access_share_5pt": {f"{k}-{k+5}": v for k, v in sorted(hist.items())},
        "example_mirror_p95_practice": {"total_items": example["total"], "wr_items": example["wr_items"],
                                        "wr_share_pct": round(100 * ex_m["wr_share"], 1),
                                        "icb_peer_median_pct": round(100 * ex_m["peer_median"], 1),
                                        "icb_percentile": ex_m["percentile"], "icb_peers": len(by_icb[example["ICB_CODE"]])},
        "unclassified_chemicals": sorted({r["CHEMICAL_SUBSTANCE_BNF_DESCR"] for r in chem if cat[r["BNF_CHEMICAL_SUBSTANCE"]] == "Unclassified"}),
    }
    json.dump(out, open(os.path.join(HERE, "data", f"evidence-{month}.json"), "w"), indent=1)
    json.dump(cat, open(os.path.join(HERE, "data", f"bnf-chemical-to-aware-{month}.json"), "w"), indent=1)
    return out


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "EPD_202506"), indent=1))
