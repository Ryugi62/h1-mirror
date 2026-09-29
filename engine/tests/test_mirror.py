"""v0.3 — brand table, same-specialty mirror, privacy thresholds (SPEC.md §v0.3 GWT).
Brand rows are the brand → active-ingredient pairs listed in Gautham et al. 2022, Table 4 (data/brandmap-gautham2022.json)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from domain.aware import RuleTable, BrandTable, Line, prescriber_mirrors, district_view  # noqa: E402

AW = json.load(open(os.path.join(HERE, "..", "data", "aware2023.json")))
NR = json.load(open(os.path.join(HERE, "..", "data", "notrec2023.json")))["combinations"]
BR = BrandTable(json.load(open(os.path.join(HERE, "..", "data", "brandmap-gautham2022.json")))["brands"])
RT = RuleTable(AW, NR, BR)


def test_brand_lines_resolve_through_brand_table():
    assert RT.classify_label("Taxim-O 200 Tablet") == "Watch"          # cefixime
    assert RT.classify_label("Clavam 625") == "Access"                 # amoxicillin + clavulanic acid
    assert RT.classify_label("Wymox 500 Capsule") == "Access"          # amoxicillin
    assert RT.classify_label("Unknownbrand 200") == "Unclassified"     # unknown brand -> chemist maps it once


def test_generic_lines_unchanged_with_brand_table():
    assert RT.classify_label("Cefixime 200 mg + Ofloxacin 200 mg Tablets") == "Not recommended"
    assert RT.classify_label("Linezolid 600 mg Tablets") == "Reserve"


def _lines(reg, spec, pharmacy, access, watch, nr=0):
    return ([Line(reg, spec, pharmacy, "Access")] * access + [Line(reg, spec, pharmacy, "Watch")] * watch
            + [Line(reg, spec, pharmacy, "Not recommended")] * nr)


def test_mirror_compares_only_same_specialty_and_needs_min_lines():
    lines = (_lines("R1", "GP", "P1", 16, 4) + _lines("R2", "GP", "P2", 12, 8, nr=2) + _lines("R3", "GP", "P3", 18, 2)
             + _lines("C1", "Chest", "P1", 2, 18) + _lines("R4", "GP", "P4", 3, 2))
    m = prescriber_mirrors(lines, min_lines=20)
    assert set(m) == {"R1", "R2", "R3", "C1"}                  # R4 has 5 lines -> no letter
    assert m["R2"]["peers"] == 3 and m["C1"]["peers"] == 1     # chest physician is not ranked against GPs
    assert abs(m["R2"]["wr_share"] - 0.4) < 1e-9 and m["R2"]["not_recommended"] == 2
    assert m["R2"]["peer_median"] == 0.2 and m["R2"]["above_median"] is True


def test_unregistered_lines_never_get_a_letter():
    lines = _lines(None, "GP", "P1", 10, 30)
    assert prescriber_mirrors(lines, min_lines=20) == {}


def test_district_view_needs_ten_pharmacies_and_has_no_names():
    few = [Line("R1", "GP", f"P{i}", "Access") for i in range(9)]
    assert district_view(few, min_pharmacies=10) is None
    many = [Line(f"R{i}", "GP", f"P{i}", "Watch" if i % 2 else "Access") for i in range(12)]
    v = district_view(many, min_pharmacies=10)
    assert v["pharmacies"] == 12 and abs(v["access_share"] - 0.5) < 1e-9
    assert not any(k in json.dumps(v) for k in ("P1", "R1"))


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); n += 1
    print(f"{n} passed")
