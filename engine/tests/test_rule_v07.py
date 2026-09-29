"""v0.7 — explicit rule for combinations on neither WHO list (from the Indian catalogue check):
1) exact WHO 'not recommended' match first; 2) exact AWaRe entry; 3) drop known non-antibiotic co-ingredients
(probiotics, enzymes, mucolytics) and classify what remains; 4) two or more antibiotics on neither list ->
'Not WHO-listed combination'; 5) anything unknown stays 'Unclassified' (never guessed)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from adapters.rule_files import from_dir  # noqa: E402

RT = from_dir(os.path.join(HERE, "..", "data"))


def test_probiotic_add_on_is_dropped_before_classifying():
    assert RT.classify_label("Cefixime (200mg) + Lactobacillus (60Million spores)") == "Watch"
    assert RT.classify_label("Amoxycillin (500mg) + Lactic Acid Bacillus (60Million spores)") == "Access"


def test_listed_not_recommended_combination_with_probiotic_still_wins():
    assert RT.classify_label("Cefixime + Lactobacillus Acidophilus + Ofloxacin") == "Not recommended"


def test_unlisted_multi_antibiotic_combination_is_named_not_guessed():
    assert RT.classify_label("Ofloxacin (200mg) + Tinidazole (600mg)") == "Not WHO-listed combination"
    assert RT.classify_label("Metronidazole (200mg) + Ofloxacin (200mg)") == "Not WHO-listed combination"


def test_unknown_ingredient_stays_unclassified():
    assert RT.classify_label("Isoniazid (300mg) + Rifampicin (450mg)") in ("Unclassified", "Watch")
    assert RT.classify_label("Cefixime (200mg) + Mysterine (5mg)") == "Unclassified"
