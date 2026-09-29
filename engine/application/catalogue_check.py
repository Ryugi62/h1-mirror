"""Use case: how much of a real Indian antibiotic market can the one rule table classify? Pure (no I/O).
Scope = systemic antibiotics (WHO AWaRe covers systemic use): products whose composition names at least one AWaRe
molecule, still marketed, not a topical / eye / ear / vaginal form."""
import re
from collections import Counter, namedtuple

from domain.aware import RuleTable, parse_label

Product = namedtuple("Product", "name composition pack discontinued")
LOCAL_FORM = re.compile(r"\b(cream|ointment|gel|drops?|lotion|soap|dusting|eye|ear|nasal|vaginal|pessary|mouth ?wash|"
                        r"spray|shampoo|paint|suppository|lozenge|solution for topical|eye/ear|ophthalmic|otic|"
                        r"face wash|serum)\b", re.I)
INJECTABLE_PACK = re.compile(r"\b(vial|ampoule|injection|infusion|bottle of \d+ ?ml solution for infusion)\b", re.I)


def molecules(rules: RuleTable) -> set:
    names = set()
    for key in list(rules.aware) + [k for route in rules.by_route.values() for k in route]:
        names |= set(key)
    return names


def is_systemic_antibiotic(p: Product, mols: set) -> bool:
    if p.discontinued or not p.composition:
        return False
    if LOCAL_FORM.search(p.name) or LOCAL_FORM.search(p.pack):
        return False
    return any(m in mols for m in parse_label(p.composition))


def label_for(p: Product) -> str:
    """The composition as a bill line, carrying the route (Injection) when the product is an injectable."""
    inj = INJECTABLE_PACK.search(p.pack) or re.search(r"\b(injection|infusion)\b", p.name, re.I)
    return p.composition + (" Injection" if inj else "")


def check(products: list, rules: RuleTable) -> dict:
    mols = molecules(rules)
    scope = [p for p in products if is_systemic_antibiotic(p, mols)]
    verdicts = Counter()
    unclassified = Counter()
    for p in scope:
        v = rules.classify_label(label_for(p))
        verdicts[v] += 1
        if v == "Unclassified":
            unclassified[" + ".join(sorted(parse_label(p.composition)))] += 1
    n = len(scope)
    classified = n - verdicts["Unclassified"]
    # de-duplicated view: one row per distinct (product name without pack/form, composition)
    uniq = {}
    for p in scope:
        uniq.setdefault((re.sub(r"\s+", " ", p.name.lower()).strip(), p.composition.lower()), p)
    dv = Counter(rules.classify_label(label_for(p)) for p in uniq.values())
    u = len(uniq)
    return {"products_total": len(products), "systemic_antibiotic_products": n,
            "by_verdict": dict(verdicts.most_common()),
            "classified_pct": round(100 * classified / n, 1) if n else None,
            "not_recommended_pct": round(100 * verdicts["Not recommended"] / n, 1) if n else None,
            "not_who_listed_pct": round(100 * verdicts["Not WHO-listed combination"] / n, 1) if n else None,
            "dedup_rule": "one row per distinct (product name, composition); counts are listed products, not sales",
            "unique_products": u,
            "unique_classified_pct": round(100 * (u - dv["Unclassified"]) / u, 1) if u else None,
            "unique_not_recommended_pct": round(100 * dv["Not recommended"] / u, 1) if u else None,
            "top_unclassified": unclassified.most_common(15)}


def brand_table(products: list, rules: RuleTable, brand_of) -> dict:
    """brand -> composition for in-scope products (first seen wins; identical brand names with different
    compositions are dropped as ambiguous)."""
    mols = molecules(rules)
    seen, ambiguous = {}, set()
    for p in products:
        if not is_systemic_antibiotic(p, mols):
            continue
        b = brand_of(p.name)
        if any(m in mols for m in parse_label(b)):
            continue                              # generic-named product ('Cefixime 200 Tablet'): the rule table reads it
        if b in seen and seen[b] != p.composition:
            ambiguous.add(b)
        seen.setdefault(b, p.composition)
    return {b: c for b, c in seen.items() if b not in ambiguous}
