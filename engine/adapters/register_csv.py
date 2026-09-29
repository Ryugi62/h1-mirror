"""Adapter: a pharmacy's month of antibiotic lines as CSV (billing-software export or confirmed register rows).

Columns: date, pharmacy, prescriber_reg, specialty, drug_line, qty. Patient columns, if present, are ignored and
never reach the engine. An empty prescriber_reg = unregistered prescriber (district aggregate only, never a letter)."""
import csv
import io

from application.monthly_mirror import RegisterRow

COLUMNS = ("date", "pharmacy", "prescriber_reg", "specialty", "drug_line", "qty")


def parse(text: str) -> list:
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}")
    rows = []
    for rec in reader:
        if not (rec.get("drug_line") or "").strip():
            continue
        rows.append(RegisterRow(*((rec.get(c) or "").strip() for c in COLUMNS)))
    return rows


def dump(rows: list) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([getattr(r, c) for c in COLUMNS])
    return out.getvalue()
