"""v0.2 — Indian register/bill labels: parse generic label -> components -> AWaRe or WHO 'not recommended'.
Given/When/Then from SPEC.md §GWT (v0.2). Fixtures are label *formats* seen on Indian packs, not sales data."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from domain.aware import classify, parse_label, RuleTable  # noqa: E402

AW = json.load(open(os.path.join(HERE, "..", "data", "aware2023.json")))
NR = json.load(open(os.path.join(HERE, "..", "data", "notrec2023.json")))["combinations"]
RT = RuleTable(AW, NR)


def test_not_recommended_list_matches_who_sheet():
    assert len(NR) == 103
    assert len(RT.not_recommended) >= 95  # salt-variants collapse (e.g. cefuroxime axetil/clavulanic acid)


def test_parse_strips_dose_form_and_spelling():
    assert parse_label("Cefixime 200 mg Tablets IP") == ["cefixime"]
    assert parse_label("Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets") == ["amoxicillin", "clavulanic acid"]
    assert parse_label("Ofloxacin 200mg & Ornidazole 500mg Tab") == ["ofloxacin", "ornidazole"]


def test_indian_single_drugs():
    assert RT.classify_label("Cefixime 200 mg Tablets IP") == "Watch"
    assert RT.classify_label("Azithromycin 500 mg Tablets") == "Watch"
    assert RT.classify_label("Amoxycillin 500 mg Capsules") == "Access"
    assert RT.classify_label("Linezolid 600 mg Tablets") == "Reserve"


def test_indian_combinations():
    assert RT.classify_label("Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets") == "Access"
    assert RT.classify_label("Cefixime 200 mg + Ofloxacin 200 mg Tablets") == "Not recommended"
    assert RT.classify_label("Ofloxacin 200mg & Ornidazole 500mg Tab") == "Not recommended"
    assert RT.classify_label("Cefpodoxime Proxetil 200 mg + Clavulanate Potassium 125 mg") == "Not recommended"


def test_label_path_agrees_with_epd_path():
    for name in ["Clarithromycin", "Amoxicillin", "Linezolid", "Doxycycline", "Nitrofurantoin"]:
        assert RT.classify_label(name) == classify(name, AW)
    assert RT.classify_label("Isoniazid 300 mg") == "Unclassified"


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); n += 1
    print(f"{n} passed")
