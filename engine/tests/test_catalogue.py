"""v0.6 — real Indian catalogue check (adapter + use case) on a few rows in the catalogue's own format."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from adapters import india_catalogue  # noqa: E402
from adapters.rule_files import from_dir  # noqa: E402
from application.catalogue_check import brand_table, check  # noqa: E402
from domain.aware import BrandTable, RuleTable  # noqa: E402

RT = from_dir(os.path.join(HERE, "..", "data"))
CSV = """id,name,price(₹),Is_discontinued,manufacturer_name,type,pack_size_label,short_composition1,short_composition2
1,Augmentin 625 Duo Tablet,223.42,FALSE,GSK,allopathy,strip of 10 tablets,Amoxycillin  (500mg) , Clavulanic Acid (125mg)
2,Azithral 500 Tablet,132.36,FALSE,Alembic,allopathy,strip of 5 tablets,Azithromycin (500mg),
3,Oflox-OZ Tablet,90,FALSE,Cipla,allopathy,strip of 10 tablets,Ofloxacin (200mg) , Ornidazole (500mg)
4,Zosyn 4.5gm Injection,500,FALSE,Pfizer,allopathy,vial of 1 Injection,Piperacillin (4000mg) , Tazobactum (500mg)
5,Neosporin Cream,80,FALSE,GSK,allopathy,tube of 10 gm Cream,Neomycin (0.5%) , Polymyxin B (5000IU)
6,Crocin 650 Tablet,30,FALSE,GSK,allopathy,strip of 15 tablets,Paracetamol (650mg),
7,Oldmox 500 Capsule,20,TRUE,X,allopathy,strip of 10 capsules,Amoxycillin (500mg),
"""


def test_catalogue_scope_and_verdicts():
    res = check(india_catalogue.parse(CSV), RT)
    assert res["products_total"] == 7 and res["systemic_antibiotic_products"] == 4   # no cream, paracetamol, discontinued
    assert res["by_verdict"] == {"Access": 1, "Watch": 2, "Not recommended": 1} and res["classified_pct"] == 100.0


def test_catalogue_brand_table_resolves_bill_lines():
    brands = brand_table(india_catalogue.parse(CSV), RT, india_catalogue.brand_of)
    assert brands["Augmentin 625 Duo"].startswith("Amoxycillin") and "Neosporin" not in brands
    rt = RuleTable(RT_AW, RT_NR, BrandTable(brands))
    assert rt.classify_label("Augmentin 625 Duo Tablet") == "Access"
    assert rt.classify_label("Oflox-OZ Tablet") == "Not recommended"
    assert rt.classify_label("Azithral 500 Tablet") == "Watch"


import json  # noqa: E402
RT_AW = json.load(open(os.path.join(HERE, "..", "data", "aware2023.json")))
RT_NR = json.load(open(os.path.join(HERE, "..", "data", "notrec2023.json")))["combinations"]


def test_national_brand_table_keeps_every_published_verdict():
    """With ~50k Indian brands merged in, every label verdict from the earlier tests must stay the same."""
    nat = from_dir(os.path.join(HERE, "..", "data"), national=True)
    cases = {"Taxim-O 200 Tablet": "Watch", "Clavam 625": "Access", "Wymox 500 Capsule": "Access",
             "Cefixime 200 mg + Ofloxacin 200 mg Tablets": "Not recommended", "Linezolid 600 mg Tablets": "Reserve",
             "Ofloxacin 200mg & Ornidazole 500mg Tab": "Not recommended", "Cefixime 200 mg Tablets IP": "Watch",
             "Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets": "Access", "Metronidazole 400 mg Tablets": "Access",
             "Minocycline 100 mg Injection": "Reserve", "Azithral 500 Tablet": "Watch", "Augmentin 625 Duo Tablet": "Access"}
    got = {k: nat.classify_label(k) for k in cases}
    assert got == cases


def test_blind_reader_audit_on_200_real_indian_products_reproduces():
    import subprocess
    repo = os.path.join(HERE, "..", "..")
    subprocess.run([sys.executable, os.path.join(repo, "audit", "score_audit.py")], check=True, capture_output=True)
    res = json.load(open(os.path.join(repo, "audit", "results.json")))
    assert res["n"] == 200 and res["agree"] == 200
