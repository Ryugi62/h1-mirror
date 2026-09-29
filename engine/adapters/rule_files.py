"""Adapter: build the one auditable RuleTable from the JSON files in engine/data (WHO AWaRe 2023, WHO
'not recommended' FDC sheet, brand table). Accepts either a directory path or already-loaded JSON strings
(the browser demo fetches the same files and passes their text)."""
import json
import os

from domain.aware import BrandTable, RuleTable

FILES = {"aware": "aware2023.json", "notrec": "notrec2023.json", "brands": "brandmap-gautham2022.json"}


def from_json_text(aware: str, notrec: str, brands: str) -> RuleTable:
    return RuleTable(json.loads(aware), json.loads(notrec)["combinations"],
                     BrandTable(json.loads(brands)["brands"]))


def from_dir(data_dir: str) -> RuleTable:
    text = {k: open(os.path.join(data_dir, f), encoding="utf-8").read() for k, f in FILES.items()}
    return from_json_text(text["aware"], text["notrec"], text["brands"])
