"""v0.6 — spellings seen in a public Indian medicine catalogue (compositions as printed by Indian manufacturers)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from adapters.rule_files import from_dir  # noqa: E402

RT = from_dir(os.path.join(HERE, "..", "data"))


def test_indian_spelling_tazobactum_is_tazobactam():
    assert RT.classify_label("Piperacillin (4000mg) + Tazobactum (500mg) Injection") == "Watch"
    assert RT.classify_label("Ceftriaxone (1000mg) + Tazobactum (125mg) Injection") == "Not recommended"


def test_catalogue_composition_format_with_brackets():
    assert RT.classify_label("Amoxycillin  (500mg) + Clavulanic Acid (125mg)") == "Access"
    assert RT.classify_label("Azithromycin (500mg)") == "Watch"
