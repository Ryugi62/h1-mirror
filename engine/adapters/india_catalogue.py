"""Adapter: a public Indian medicine catalogue (junioralive/Indian-Medicine-Dataset, MIT licence; one row per brand
product: name, manufacturer, pack, composition as printed). Used to (1) measure how many real Indian antibiotic
products the rule table can classify and (2) build a national brand table (brand -> composition)."""
import csv
import io
import re

from application.catalogue_check import Product

SOURCE_URL = ("https://raw.githubusercontent.com/junioralive/Indian-Medicine-Dataset/main/DATA/"
              "indian_medicine_data.csv")
FORM_TAIL = re.compile(r"\s+(?:dry syrup|oral suspension|suspension|syrup|tablet dt|tablets?|capsules?|injection|"
                       r"infusion|drops?|redimix|kid tablet|dt|sachet|granules|powder for oral suspension)\s*$", re.I)


def parse(text: str) -> list:
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        comp = " + ".join(x.strip() for x in (r.get("short_composition1", ""), r.get("short_composition2", ""))
                          if x and x.strip())
        out.append(Product(name=r["name"].strip(), composition=comp, pack=r.get("pack_size_label", "").strip(),
                           discontinued=r.get("Is_discontinued", "").strip().upper() == "TRUE"))
    return out


def brand_of(name: str) -> str:
    """'Augmentin 625 Duo Tablet' -> 'Augmentin 625 Duo' (the form word is kept on the bill line, so strip it)."""
    return FORM_TAIL.sub("", name).strip()
