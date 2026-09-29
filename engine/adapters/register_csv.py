"""Adapter: a pharmacy's month of antibiotic lines as CSV (billing-software export or confirmed register rows).

Columns: date, pharmacy, prescriber_reg, specialty, drug_line, qty [, source]. source = "bill" (default: complete
billing-software export) or "h1_photo" (photographed H1 register row; aggregate only). Patient columns, if present, are
ignored and never reach the engine. An empty prescriber_reg = unregistered prescriber (district aggregate only, never a letter)."""
import csv
import io

from application.monthly_mirror import RegisterRow

COLUMNS = ("date", "pharmacy", "prescriber_reg", "specialty", "drug_line", "qty")
OPTIONAL = ("source", "prescriber_name")


def parse(text: str) -> list:
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}")
    rows = []
    for rec in reader:
        if not (rec.get("drug_line") or "").strip():
            continue
        source = (rec.get("source") or "").strip() or "bill"
        rows.append(RegisterRow(*((rec.get(c) or "").strip() for c in COLUMNS), source=source,
                                prescriber_name=(rec.get("prescriber_name") or "").strip()))
    return rows


def dump(rows: list) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(COLUMNS + OPTIONAL)
    for r in rows:
        w.writerow([getattr(r, c) for c in COLUMNS + OPTIONAL])
    return out.getvalue()
