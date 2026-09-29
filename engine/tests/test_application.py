"""v0.4 — use case 'monthly mirror' end to end: CSV lines -> letters + district view (SPEC.md §v0.4)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
from adapters import register_csv  # noqa: E402
from adapters.letter_html import letter_html, letter_text  # noqa: E402
from adapters.rule_files import from_dir  # noqa: E402
from application.monthly_mirror import RegisterRow, classify_lines, run_month  # noqa: E402

RT = from_dir(os.path.join(ROOT, "data"))
SAMPLE = os.path.join(ROOT, "..", "examples", "register-sample.csv")


def _rows(reg, spec, pharmacy, access, watch, fdc=0):
    mk = lambda drug: RegisterRow("2026-08-01", pharmacy, reg, spec, drug, "10 tab")
    return ([mk("Clavam 625")] * access + [mk("Taxim-O 200 Tablet")] * watch
            + [mk("Cefixime 200 mg + Ofloxacin 200 mg Tablets")] * fdc)


def test_given_register_rows_when_month_runs_then_letters_name_discouraged_combinations():
    rows = (_rows("R1", "GP", "P1", 16, 4) + _rows("R2", "GP", "P2", 12, 8, fdc=3) + _rows("R3", "GP", "P3", 18, 2)
            + _rows(None, "Unregistered", "P1", 0, 30))
    rep = run_month(rows, RT, "2026-08", min_lines=20, min_pharmacies=10)
    assert set(rep.letters) == {"R1", "R2", "R3"}                     # unregistered lines never get a letter
    r2 = rep.letters["R2"]
    assert abs(r2.wr_share - 0.4) < 1e-9 and r2.peers == 3 and r2.above_median is True
    assert r2.not_recommended == [("Cefixime 200 mg + Ofloxacin 200 mg Tablets", 3)]
    assert r2.top_watch_reserve == [("Taxim-O 200 Tablet", 8)]
    assert rep.district is None                                        # 3 pharmacies < 10
    assert rep.unregistered_lines == 30 and rep.lines_total == 93


def test_letter_is_private_and_says_pattern_not_verdict():
    rep = run_month(_rows("R1", "GP", "P1", 16, 4) + _rows("R2", "GP", "P2", 12, 8), RT, "2026-08")
    html, text = letter_html(rep.letters["R2"]), letter_text(rep.letters["R2"])
    assert "40.0%" in html and "R2" in html and "P2" not in html        # no pharmacy name in a letter
    assert "pattern, not a verdict" in text and "R1" not in text          # no other prescriber named


def test_csv_adapter_round_trip_and_rejects_missing_columns():
    rows = _rows("R9", "ENT", "P9", 1, 1)
    assert register_csv.parse(register_csv.dump(rows)) == rows
    try:
        register_csv.parse("date,drug_line\n2026-08-01,Clavam 625\n")
    except ValueError as e:
        assert "prescriber_reg" in str(e)
    else:
        raise AssertionError("missing columns accepted")


def test_sample_month_gives_letters_district_view_and_flags_unknown_brand():
    rows = register_csv.parse(open(SAMPLE, encoding="utf-8").read())
    rep = run_month(rows, RT, "2026-08")
    assert rep.lines_total == len(rows) and len(rep.letters) == 30            # every registered prescriber >= 20 lines
    assert {lt.specialty for lt in rep.letters.values()} == {"General practice", "Paediatrics", "ENT"}
    assert rep.district is not None and rep.district["pharmacies"] == 12
    assert ("Zifi 200 Tablet" in dict(rep.unclassified_labels))              # chemist maps a new brand once
    assert all(lt.peers >= 5 for lt in rep.letters.values())


def test_classify_lines_for_the_demo_box():
    out = classify_lines(["Taxim-O 200 Tablet", "", "  Linezolid 600 mg Tablets "], RT)
    assert out == [("Taxim-O 200 Tablet", "Watch"), ("Linezolid 600 mg Tablets", "Reserve")]


def test_chemist_gets_own_printable_register_only():
    from application.monthly_mirror import pharmacy_register
    from adapters.letter_html import register_html
    rows = _rows("R1", "GP", "P1", 2, 1) + _rows("R2", "GP", "P2", 5, 5) + _rows(None, "Unregistered", "P1", 0, 1)
    reg = pharmacy_register(rows, RT, "P1")
    assert len(reg) == 4 and {e.verdict for e in reg} == {"Access", "Watch"}
    assert [e.prescriber for e in reg].count("unregistered") == 1
    html = register_html("P1", "2026-08", reg)
    assert "P1" in html and "R2" not in html and html.count("<tr>") == 5   # header + 4 lines, no other pharmacy
