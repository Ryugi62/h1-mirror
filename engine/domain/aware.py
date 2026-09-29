"""H1 Mirror domain rules: WHO AWaRe classification + prescriber mirror indicators. Pure: no I/O, no SDK."""
import re
from statistics import median

# Where the dispensing name differs from the WHO AWaRe 2023 name (route noted when the WHO list splits by route).
OVERRIDES = {
    "co-amoxiclav": "amoxicillin/clavulanic-acid",
    "co-trimoxazole": "sulfamethoxazole/trimethoprim",
    "metronidazole": "metronidazole_oral",
    "fosfomycin": "fosfomycin_oral",
    "vancomycin": "vancomycin_oral",
    "minocycline": "minocycline_oral",
    "colistimethate": "colistin_iv",  # route not separable in the source; every colistin entry is Reserve
    "fusidic acid": "fusidic-acid",
    "sodium fusidate": "fusidic-acid",
}
SALT_SUFFIXES = (" sodium", " hydrochloride", " hyclate", " monohydrate", " trometamol", " sulfate",
                 " pentahydrate", " axetil", " stearate", " ethylsuccinate", " combined preparations", " hippurate")
CATEGORIES = ("Access", "Watch", "Reserve")


def normalise(drug_name: str) -> str:
    n = re.sub(r"\(.*?\)", "", drug_name.lower()).strip()
    if n == "sodium fusidate":
        return n
    for s in SALT_SUFFIXES:
        n = n.replace(s, "")
    return n.strip()


def classify(drug_name: str, aware_table: dict) -> str:
    """aware_table: {who_name_lowercase: [category, atc, class]} from the WHO AWaRe 2023 sheet."""
    key = normalise(drug_name)
    hit = aware_table.get(OVERRIDES.get(key, key))
    return hit[0] if hit else "Unclassified"


def shares(access_items: int, watch_reserve_items: int) -> dict:
    classified = access_items + watch_reserve_items
    if classified == 0:
        return {"access_share": None, "wr_share": None}
    return {"access_share": access_items / classified, "wr_share": watch_reserve_items / classified}


def mirror(prescriber_wr_share: float, peer_wr_shares: list) -> dict:
    """Social-norm feedback input: where one prescriber sits against peers (same area)."""
    peers = sorted(peer_wr_shares)
    below = sum(1 for p in peers if p < prescriber_wr_share)
    return {
        "wr_share": prescriber_wr_share,
        "peer_median": median(peers),
        "percentile": round(100 * below / len(peers)),
        "above_median": prescriber_wr_share > median(peers),
    }


# ---- v0.2: Indian register / bill labels (generic names as printed on Indian packs) --------------------------
DOSE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|µg|ml|iu|%)?(?=\s|$|[+&,/)])", re.I)
FORM_WORDS = {"tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps", "ip", "bp", "usp", "oral",
              "suspension", "syrup", "dry", "powder", "for", "injection", "inj", "dispersible", "dt", "sr", "er", "xr",
              "film", "coated", "kid", "forte", "sachet", "sachets", "granules", "infusion", "vial"}
SPELLING = {"amoxycillin": "amoxicillin", "cephalexin": "cefalexin", "sulphamethoxazole": "sulfamethoxazole",
            "potassium clavulanate": "clavulanic acid", "clavulanate potassium": "clavulanic acid",
            "clavulanate": "clavulanic acid", "diluted potassium clavulanate": "clavulanic acid",
            "tazobactum": "tazobactam", "sulbactum": "sulbactam"}   # v0.6: spellings in Indian catalogue compositions
EXTRA_SALTS = (" proxetil", " potassium", " disodium")
INJECTABLE = re.compile(r"\b(?:inj|injection|infusion|iv|i\.v\.|vial)\b", re.I)
# v0.7: co-ingredients that are not antibiotics (dropped before classifying the antibiotic part; never guessed otherwise)
NON_ANTIBIOTIC = re.compile(r"^(?:lactobacillus|lactic acid bacillus|lactic acid|bacillus clausii|bacillus coagulans|"
                            r"saccharomyces|streptococcus faecalis|clostridium butyricum|bifidobacterium|lactic ferments|"
                            r"serratiopeptidase|serrapeptase|bromelain|bromelains|trypsin|chymotrypsin|ambroxol|bromhexine)\b")
NOT_LISTED = "Not WHO-listed combination"
SPLIT = re.compile(r"\s*(?:\+|&|/|,|\band\b|\bwith\b)\s*", re.I)


def _canonical(component: str) -> str:
    c = component.lower().replace("-", " ").strip()
    c = SPELLING.get(c, c)
    c = normalise(c)
    for s in EXTRA_SALTS:
        c = c.replace(s, "")
    return SPELLING.get(c.strip(), c.strip())


def parse_label(label: str) -> list:
    """'Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets' -> ['amoxicillin', 'clavulanic acid']"""
    text = re.sub(r"\(.*?\)", " ", label)
    parts = []
    for raw in SPLIT.split(text):
        words = [w for w in DOSE.sub(" ", raw).split() if w.lower() not in FORM_WORDS]
        if words:
            parts.append(_canonical(" ".join(words)))
    return parts


class BrandTable:
    """Brand -> composition, e.g. 'Taxim-O' -> 'cefixime'. Longest brand prefix wins; the rest (strength) is kept.
    Indexed by first word so a national catalogue (tens of thousands of brands) stays fast (v0.6)."""

    def __init__(self, brands: dict):
        self.index = {}
        for b, c in brands.items():
            low = b.lower().strip()
            if low:
                self.index.setdefault(low.split()[0], []).append((low, c))
        for lst in self.index.values():
            lst.sort(key=lambda x: -len(x[0]))

    def resolve(self, label: str) -> str:
        low = label.strip().lower()
        if not low:
            return label
        first = low.split()[0]
        candidates = self.index.get(first, [])
        if not candidates:                        # brand glued to strength or punctuation, e.g. 'Taxim-O200'
            candidates = [bc for k, lst in self.index.items() if low.startswith(k) for bc in lst]
            candidates.sort(key=lambda x: -len(x[0]))
        for brand, comp in candidates:
            if low == brand or (low.startswith(brand) and not low[len(brand)].isalpha()):
                return comp + label.strip()[len(brand):]
        return label


class RuleTable:
    """One auditable table: WHO AWaRe 2023 (single drugs + listed combinations) + WHO 'not recommended' FDCs
    (+ optional brand table applied first)."""

    def __init__(self, aware_table: dict, not_recommended: list, brands: "BrandTable" = None):
        self.aware = {}
        self.by_route = {"oral": {}, "iv": {}}   # WHO lists some drugs per route, e.g. 'minocycline_iv' (v0.4)
        for k, v in aware_table.items():
            if "_" in k and k.rsplit("_", 1)[1] in self.by_route:
                name, route = k.rsplit("_", 1)
                self.by_route[route][frozenset([_canonical(name)])] = v[0]
            else:
                self.aware[frozenset(_canonical(p) for p in k.split("/"))] = v[0]
        self.not_recommended = {frozenset(_canonical(p) for p in c.split("/")) for c in not_recommended}
        self.brands = brands

    def classify_label(self, label: str) -> str:
        if self.brands is not None:
            label = self.brands.resolve(label)
        key = frozenset(parse_label(label))
        if key in self.not_recommended:
            return "Not recommended"
        route = "iv" if INJECTABLE.search(label) else "oral"
        hit = self._lookup(key, route)
        if hit:
            return hit
        core = frozenset(p for p in key if not NON_ANTIBIOTIC.match(p))
        if core and core != key:                            # rule 3: drop probiotic / enzyme / mucolytic add-ons
            if core in self.not_recommended:
                return "Not recommended"
            hit = self._lookup(core, route)
            if hit:
                return hit
        if len(core) >= 2 and all(self._lookup(frozenset([p]), route) for p in core):
            return NOT_LISTED                               # rule 4: antibiotics combined, on neither WHO list
        return "Unclassified"                               # rule 5: unknown ingredient, never guessed

    def _lookup(self, key, route):
        if key in self.aware:
            return self.aware[key]
        other = "oral" if route == "iv" else "iv"
        return self.by_route[route].get(key) or self.by_route[other].get(key)


# ---- v0.3: prescriber mirror (same-specialty peers) and district view (aggregates only) ----------------------
from collections import namedtuple  # noqa: E402

Line = namedtuple("Line", "prescriber_reg specialty pharmacy category")   # prescriber_reg None = unregistered


def _mix(lines):
    c = {k: 0 for k in ("Access", "Watch", "Reserve", "Not recommended", NOT_LISTED, "Unclassified")}
    for ln in lines:
        c[ln.category] += 1
    awr = c["Access"] + c["Watch"] + c["Reserve"]
    return c, awr


def prescriber_mirrors(lines: list, min_lines: int = 20) -> dict:
    """One private mirror per registered prescriber with >= min_lines lines, ranked only against the same specialty."""
    by = {}
    for ln in lines:
        if ln.prescriber_reg:
            by.setdefault(ln.prescriber_reg, []).append(ln)
    rows = {}
    for reg, ls in by.items():
        if len(ls) < min_lines:
            continue
        c, awr = _mix(ls)
        if awr == 0:
            continue
        rows[reg] = {"specialty": ls[0].specialty, "lines": len(ls), "access_share": c["Access"] / awr,
                     "wr_share": (c["Watch"] + c["Reserve"]) / awr, "not_recommended": c["Not recommended"]}
    for reg, r in rows.items():
        peers = [x["wr_share"] for x in rows.values() if x["specialty"] == r["specialty"]]
        m = mirror(r["wr_share"], peers)
        r.update(peer_median=m["peer_median"], percentile=m["percentile"], above_median=m["above_median"], peers=len(peers))
    return rows


def district_view(lines: list, min_pharmacies: int = 10):
    """Aggregate for the district health office; None unless >= min_pharmacies contribute. No pharmacy or prescriber ids."""
    pharmacies = {ln.pharmacy for ln in lines}
    if len(pharmacies) < min_pharmacies:
        return None
    c, awr = _mix(lines)
    return {"pharmacies": len(pharmacies), "lines": len(lines),
            "access_share": c["Access"] / awr if awr else None,
            "wr_share": (c["Watch"] + c["Reserve"]) / awr if awr else None,
            "not_recommended_lines": c["Not recommended"]}
