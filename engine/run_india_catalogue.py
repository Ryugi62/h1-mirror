"""Real Indian data check: python3 engine/run_india_catalogue.py [path/to/indian_medicine_data.csv]
Downloads the public Indian medicine catalogue (MIT) if no path is given, verifies its sha256, classifies every
marketed systemic antibiotic product with the one rule table and writes
  engine/data/evidence-india-catalogue.json  (coverage, verdict mix, top unclassified compositions)
  engine/data/brandmap-india-catalogue.json  (brand -> composition, for bill lines written by brand)."""
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adapters import india_catalogue  # noqa: E402
from adapters.rule_files import from_dir  # noqa: E402
from application.catalogue_check import brand_table, check  # noqa: E402
from domain.aware import BrandTable, RuleTable  # noqa: E402

SHA256_PREFIX = "c9de0182474f652b"   # file as downloaded 2026-09-29


def main(path=None) -> dict:
    raw = open(path, "rb").read() if path else urllib.request.urlopen(india_catalogue.SOURCE_URL, timeout=120).read()
    sha = hashlib.sha256(raw).hexdigest()
    products = india_catalogue.parse(raw.decode("utf-8"))
    rules = from_dir(os.path.join(HERE, "data"))
    t0 = time.time()
    res = check(products, rules)
    brands = brand_table(products, rules, india_catalogue.brand_of)
    gautham = json.load(open(os.path.join(HERE, "data", "brandmap-gautham2022.json")))["brands"]
    low = {b.lower() for b in brands}
    res.update(source=india_catalogue.SOURCE_URL, licence="MIT (junioralive/Indian-Medicine-Dataset)",
               sha256=sha, sha256_matches_2026_09_29=sha.startswith(SHA256_PREFIX), elapsed_sec=round(time.time() - t0, 1),
               brands_in_table=len(brands),
               gautham_2022_brands_found=sorted(b for b in gautham if any(k == b.lower() or k.startswith(b.lower() + " ")
                                                                           for k in low)),
               gautham_2022_brands_total=len(gautham))
    json.dump(res, open(os.path.join(HERE, "data", "evidence-india-catalogue.json"), "w"), indent=1, ensure_ascii=False)
    json.dump({"_source": f"{india_catalogue.SOURCE_URL} (MIT). Marketed systemic antibiotic products; brand = product "
                          "name without the form word; ambiguous brand names dropped.", "brands": brands},
              open(os.path.join(HERE, "data", "brandmap-india-catalogue.json"), "w"), ensure_ascii=False)
    return res


if __name__ == "__main__":
    r = main(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: v for k, v in r.items() if k != "top_unclassified"}, ensure_ascii=False, indent=1))
    print(r["top_unclassified"][:8])
