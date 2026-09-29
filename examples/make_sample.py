"""Generate examples/register-sample.csv: ONE SYNTHETIC MONTH for a small district (no real pharmacy, prescriber or
patient). 12 pharmacies, 30 registered prescribers in 3 specialties with different prescribing habits, plus lines
from unregistered providers. Deterministic (fixed seed).  Usage: python3 examples/make_sample.py"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
from adapters.register_csv import dump  # noqa: E402
from application.monthly_mirror import RegisterRow  # noqa: E402

ACCESS = ["Clavam 625", "Wymox 500 Capsule", "Amoxycillin 500 mg Capsules", "Doxycycline 100 mg Capsules",
          "Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets", "Cephalexin 500 mg Capsules",
          "Nitrofurantoin 100 mg Capsules", "Moxileb 250 DT"]
WATCH = ["Taxim-O 200 Tablet", "Cefixime 200 mg Tablets IP", "Azithromycin 500 mg Tablets",
         "Ciprofloxacin 500 mg Tablets", "Levofloxacin 500 mg Tablets", "Monocef-O 200", "Cefuroxime 500 mg Tablets",
         "Ofloxacin 200 mg Tablets", "Clarithromycin 500 mg Tablets"]
RESERVE = ["Linezolid 600 mg Tablets", "Faropenem 200 mg Tablets"]
NOT_REC = ["Cefixime 200 mg + Ofloxacin 200 mg Tablets", "Ofloxacin 200mg & Ornidazole 500mg Tab"]
UNKNOWN = ["Zifi 200 Tablet"]  # a real-world brand not yet in the brand table -> 'Unclassified' until mapped once
QTY = ["6 tab", "10 tab", "5 cap", "15 cap", "3 tab", "14 cap", "1 strip"]
SPECIALTIES = [("General practice", 18, "GP"), ("Paediatrics", 7, "PD"), ("ENT", 5, "EN")]
MONTH = "2026-08"


def make(seed: int = 20260930) -> list:
    rng = random.Random(seed)
    pharmacies = [f"PH-{i:02d}" for i in range(1, 13)]
    rows = []
    n = 0
    for specialty, count, code in SPECIALTIES:
        for _ in range(count):
            n += 1
            reg = f"SMC-{code}-{1000 + n * 37}"
            watch_p = rng.uniform(0.10, 0.50)          # habit: share of Watch lines
            reserve_p = rng.choice([0, 0, 0, 0.01, 0.03])
            fdc_p = rng.choice([0, 0, 0.02, 0.05, 0.10])
            home = rng.sample(pharmacies, 3)             # a prescriber's patients use a few nearby chemists
            for _ in range(rng.randint(22, 90)):
                u = rng.random()
                if u < fdc_p:
                    drug = rng.choice(NOT_REC)
                elif u < fdc_p + reserve_p:
                    drug = rng.choice(RESERVE)
                elif u < fdc_p + reserve_p + watch_p:
                    drug = rng.choice(WATCH)
                elif u < fdc_p + reserve_p + watch_p + 0.01:
                    drug = rng.choice(UNKNOWN)
                else:
                    drug = rng.choice(ACCESS)
                rows.append(RegisterRow(f"2026-08-{rng.randint(1, 31):02d}", rng.choice(home), reg, specialty, drug,
                                        rng.choice(QTY)))
    for _ in range(120):                                  # unregistered providers: aggregate only, never a letter
        drug = rng.choice(WATCH + WATCH + NOT_REC + ACCESS)
        rows.append(RegisterRow(f"2026-08-{rng.randint(1, 31):02d}", rng.choice(pharmacies), "", "Unregistered",
                                drug, rng.choice(QTY)))
    rows.sort(key=lambda r: (r.date, r.pharmacy, r.prescriber_reg))
    return rows


if __name__ == "__main__":
    path = os.path.join(HERE, "register-sample.csv")
    open(path, "w", encoding="utf-8").write(dump(make()))
    print(f"wrote {path}")
