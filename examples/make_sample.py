"""Generate examples/register-sample.csv + examples/council-register-sample.txt: ONE SYNTHETIC MONTH for a small
district (no real pharmacy, prescriber or patient). 12 pharmacies: 10 export complete bills (source=bill), 2 only
photograph their handwritten H1 register (source=h1_photo: Watch/Reserve/combination lines only, aggregate only).
30 registered prescribers in 3 specialties with different habits, lines from unregistered providers, and a few
misread registration numbers that are not on the council list. Deterministic (fixed seed).
Usage: python3 examples/make_sample.py"""
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
COUNTS = ["3", "5", "6", "10", "14", "15"]
PHOTO_PHARMACIES = ("PH-11", "PH-12")
SPECIALTIES = [("General practice", 18, "GP"), ("Paediatrics", 7, "PD"), ("ENT", 5, "EN")]
MONTH = "2026-08"


def make(seed: int = 20260930):
    rng = random.Random(seed)
    pharmacies = [f"PH-{i:02d}" for i in range(1, 13)]
    rows = []
    n = 0
    for specialty, count, code in SPECIALTIES:
        for _ in range(count):
            n += 1
            reg = f"SMC-{10412 + n * 373}"      # council numbers do not encode specialty (it comes from the register)
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
                ph = rng.choice(home)
                if ph in PHOTO_PHARMACIES and drug in ACCESS + UNKNOWN:
                    continue                             # not an H1 drug: never written in the H1 register
                rows.append(RegisterRow(f"2026-08-{rng.randint(1, 31):02d}", ph, reg, specialty, drug, qty(drug, rng),
                                        "h1_photo" if ph in PHOTO_PHARMACIES else "bill"))
    for _ in range(120):                                  # unregistered providers: aggregate only, never a letter
        drug = rng.choice(WATCH + WATCH + NOT_REC + ACCESS)
        ph = rng.choice(pharmacies)
        if ph in PHOTO_PHARMACIES and drug in ACCESS:
            continue
        rows.append(RegisterRow(f"2026-08-{rng.randint(1, 31):02d}", ph, "", "Unregistered", drug, qty(drug, rng),
                                "h1_photo" if ph in PHOTO_PHARMACIES else "bill"))
    rows.sort(key=lambda r: (r.date, r.pharmacy, r.prescriber_reg))
    regs = sorted({r.prescriber_reg for r in rows if r.prescriber_reg})
    for i in range(0, 12):                                # misread numbers (e.g. a digit dropped): not on the council list
        src = rows[i * 97]
        if src.prescriber_reg:
            rows[i * 97] = src._replace(prescriber_reg=src.prescriber_reg[:-1])
    return rows, regs


def qty(drug: str, rng) -> str:
    form = "cap" if "Cap" in drug else "sachet" if "Sachet" in drug else "tab"
    return f"{rng.choice(COUNTS)} {form}"


if __name__ == "__main__":
    rows, regs = make()
    open(os.path.join(HERE, "register-sample.csv"), "w", encoding="utf-8").write(dump(rows))
    open(os.path.join(HERE, "council-register-sample.txt"), "w", encoding="utf-8").write("\n".join(regs) + "\n")
    print(f"wrote {len(rows)} lines, {len(regs)} council numbers")
