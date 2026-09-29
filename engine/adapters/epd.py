"""Adapter: NHSBSA open data portal (English Prescribing Dataset, Open Government Licence v3.0)."""
import json
import urllib.parse
import urllib.request

API = "https://opendata.nhsbsa.net/api/3/action/datastore_search_sql?"


def sql(resource: str, query: str, timeout: int = 600) -> list:
    url = API + urllib.parse.urlencode({"resource_id": resource, "sql": query})
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)["result"]["result"]["records"]


def national_by_chemical(month: str) -> list:
    return sql(month, f"SELECT BNF_CHEMICAL_SUBSTANCE, CHEMICAL_SUBSTANCE_BNF_DESCR, SUM(ITEMS) AS items "
                      f"FROM `{month}` WHERE BNF_CHEMICAL_SUBSTANCE LIKE '0501%' "
                      f"GROUP BY BNF_CHEMICAL_SUBSTANCE, CHEMICAL_SUBSTANCE_BNF_DESCR ORDER BY items DESC")


def by_practice(month: str, access_codes: list, wr_codes: list) -> list:
    q = lambda codes: ",".join(f"'{c}'" for c in codes)
    return sql(month, f"SELECT PRACTICE_CODE, ICB_CODE, SUM(ITEMS) AS total, "
                      f"SUM(CASE WHEN BNF_CHEMICAL_SUBSTANCE IN ({q(access_codes)}) THEN ITEMS ELSE 0 END) AS access_items, "
                      f"SUM(CASE WHEN BNF_CHEMICAL_SUBSTANCE IN ({q(wr_codes)}) THEN ITEMS ELSE 0 END) AS wr_items "
                      f"FROM `{month}` WHERE BNF_CHEMICAL_SUBSTANCE LIKE '0501%' GROUP BY PRACTICE_CODE, ICB_CODE")
