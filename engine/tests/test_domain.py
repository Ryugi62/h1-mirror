import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from domain.aware import classify, shares, mirror  # noqa: E402

AW = json.load(open(os.path.join(HERE, "..", "data", "aware2023.json")))


def test_classify_known_names():
    assert classify("Amoxicillin", AW) == "Access"
    assert classify("Co-amoxiclav (Amoxicillin/clavulanic acid)", AW) == "Access"
    assert classify("Clarithromycin", AW) == "Watch"
    assert classify("Fosfomycin trometamol", AW) == "Watch"
    assert classify("Linezolid", AW) == "Reserve"
    assert classify("Colistimethate sodium", AW) == "Reserve"
    assert classify("Sodium fusidate", AW) == "Watch"


def test_not_in_aware_is_unclassified():
    assert classify("Methenamine hippurate", AW) == "Unclassified"
    assert classify("Isoniazid", AW) == "Unclassified"


def test_who_table_counts_match_publication():
    cats = [v[0] for v in AW.values()]
    assert (len(cats), cats.count("Access"), cats.count("Watch"), cats.count("Reserve")) == (257, 87, 141, 29)


def test_shares_and_mirror():
    s = shares(80, 20)
    assert abs(s["access_share"] - 0.8) < 1e-9 and abs(s["wr_share"] - 0.2) < 1e-9
    m = mirror(0.20, [0.10, 0.16, 0.16, 0.30])
    assert m["peer_median"] == 0.16 and m["above_median"] is True and m["percentile"] == 75
    assert shares(0, 0)["access_share"] is None


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); n += 1
    print(f"{n} passed")
