"""v0.4 — WHO AWaRe 2023 lists some antibiotics per route (e.g. 'metronidazole_oral', 'minocycline_iv').
Indian labels carry the route in the form word (Tablets / Capsules vs Injection), so the label path must pick it."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from adapters.rule_files import from_dir  # noqa: E402

RT = from_dir(os.path.join(HERE, "..", "data"))


def test_route_split_drugs_are_classified_from_the_label_form():
    assert RT.classify_label("Metronidazole 400 mg Tablets") == "Access"
    assert RT.classify_label("Minocycline 100 mg Capsules") == "Watch"      # minocycline_oral
    assert RT.classify_label("Minocycline 100 mg Injection") == "Reserve"   # minocycline_iv
    assert RT.classify_label("Fosfomycin 3 g Sachet") == "Watch"            # fosfomycin_oral
    assert RT.classify_label("Fosfomycin 4 g Inj") == "Reserve"             # fosfomycin_iv
    assert RT.classify_label("Vancomycin 1 g Injection") == "Watch"


def test_every_route_split_entry_is_reachable():
    aw = json.load(open(os.path.join(HERE, "..", "data", "aware2023.json")))
    for key, (category, _atc, _cls) in aw.items():
        if "_" not in key:
            continue
        name, route = key.rsplit("_", 1)
        form = "Injection" if route == "iv" else "Tablets"
        assert RT.classify_label(f"{name.replace('-', ' ')} 100 mg {form}") == category, key
