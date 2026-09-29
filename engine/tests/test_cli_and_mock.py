"""Reproducibility: the CLI runs on the sample month; the blind mock-register reading test re-scores to the
published numbers (40/40 verdicts, 35/40 registration digits, 34/40 quantity)."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")


def test_cli_writes_one_letter_per_eligible_prescriber():
    with tempfile.TemporaryDirectory() as out:
        subprocess.run([sys.executable, os.path.join(REPO, "engine", "cli.py"),
                        os.path.join(REPO, "examples", "register-sample.csv"), "--out", out,
                        "--council", os.path.join(REPO, "examples", "council-register-sample.txt")], check=True,
                       capture_output=True)
        summary = json.load(open(os.path.join(out, "district.json")))
        assert len(os.listdir(os.path.join(out, "letters"))) == summary["letters"] > 0
        assert summary["district"]["pharmacies"] == 12 and summary["unmatched_reg_lines"] > 0


def test_mock_register_reading_scores_reproduce():
    mt = os.path.join(REPO, "mocktest")
    with tempfile.TemporaryDirectory() as out:
        res_path = os.path.join(out, "r.json")
        subprocess.run([sys.executable, os.path.join(mt, "score_mock.py"), os.path.join(mt, "truth.json"),
                        os.path.join(mt, "predictions-haiku-2026-09-26.jsonl"), res_path], check=True,
                       capture_output=True)
        c = json.load(open(res_path))["correct"]
    assert (c["verdict"], c["drug_line"], c["strength"], c["reg_digits"], c["qty"]) == (40, 40, 40, 35, 34)
