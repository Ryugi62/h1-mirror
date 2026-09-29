"""Use case: one month of register/bill lines -> private prescriber mirrors + district aggregate.

Pure orchestration of the domain rules (no files, no network, no framework). The same module runs in the CLI
(`engine/cli.py`) and, unchanged, in the browser demo (`index.html`, via Pyodide)."""
from collections import Counter, namedtuple

from domain.aware import Line, RuleTable, district_view, prescriber_mirrors

# One row as a chemist records it (Schedule H1 register or bill export). Patient fields never enter the engine.
RegisterRow = namedtuple("RegisterRow", "date pharmacy prescriber_reg specialty drug_line qty")

Letter = namedtuple("Letter", "prescriber_reg specialty month lines access_share wr_share peer_median percentile "
                              "peers above_median not_recommended top_watch_reserve")

MonthReport = namedtuple("MonthReport", "month letters district lines_total unclassified_lines unclassified_labels "
                                        "unregistered_lines")

WR = ("Watch", "Reserve")


def run_month(rows: list, rules: RuleTable, month: str, min_lines: int = 20, min_pharmacies: int = 10) -> MonthReport:
    """Classify every row with the one rule table, then build letters (registered prescribers with >= min_lines,
    ranked only against the same specialty) and the district view (None below min_pharmacies)."""
    verdicts = [rules.classify_label(r.drug_line) for r in rows]
    lines = [Line(r.prescriber_reg or None, r.specialty, r.pharmacy, v) for r, v in zip(rows, verdicts)]
    mirrors = prescriber_mirrors(lines, min_lines=min_lines)

    per_reg_nr, per_reg_wr = {}, {}
    for r, v in zip(rows, verdicts):
        if not r.prescriber_reg:
            continue
        if v == "Not recommended":
            per_reg_nr.setdefault(r.prescriber_reg, Counter())[_tidy(r.drug_line)] += 1
        elif v in WR:
            per_reg_wr.setdefault(r.prescriber_reg, Counter())[_tidy(r.drug_line)] += 1

    letters = {}
    for reg, m in mirrors.items():
        letters[reg] = Letter(
            prescriber_reg=reg, specialty=m["specialty"], month=month, lines=m["lines"],
            access_share=m["access_share"], wr_share=m["wr_share"], peer_median=m["peer_median"],
            percentile=m["percentile"], peers=m["peers"], above_median=m["above_median"],
            not_recommended=sorted(per_reg_nr.get(reg, Counter()).items(), key=lambda kv: (-kv[1], kv[0])),
            top_watch_reserve=per_reg_wr.get(reg, Counter()).most_common(3))

    unclassified = Counter(_tidy(r.drug_line) for r, v in zip(rows, verdicts) if v == "Unclassified")
    return MonthReport(
        month=month, letters=letters, district=district_view(lines, min_pharmacies=min_pharmacies),
        lines_total=len(rows), unclassified_lines=sum(unclassified.values()),
        unclassified_labels=unclassified.most_common(), unregistered_lines=sum(1 for r in rows if not r.prescriber_reg))


def classify_lines(labels: list, rules: RuleTable) -> list:
    """[(label, verdict)] for free-text lines as written on a bill or register (demo tab 1)."""
    return [(lb.strip(), rules.classify_label(lb)) for lb in labels if lb.strip()]


def _tidy(label: str) -> str:
    return " ".join(label.split())


RegisterEntry = namedtuple("RegisterEntry", "date prescriber drug_line qty verdict")


def pharmacy_register(rows: list, rules: RuleTable, pharmacy: str) -> list:
    """The chemist's own month, ready to print for inspection: only this pharmacy's lines, each with its rule-table
    group. Patient details stay on the chemist's own copy and never enter the engine."""
    return [RegisterEntry(r.date, r.prescriber_reg or "unregistered", _tidy(r.drug_line), r.qty,
                          rules.classify_label(r.drug_line))
            for r in sorted(rows, key=lambda r: (r.date, r.prescriber_reg or "")) if r.pharmacy == pharmacy]
