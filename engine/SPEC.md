# H1 Mirror engine — SPEC (v0.4, 2026-09-30; v0.3/v0.2 2026-09-26; v0.1 2026-09-25)

## Purpose
Classify every antibiotic dispensing/prescribing record against the WHO AWaRe 2023 list and turn the result into
prescriber-level "mirror" indicators (Access share, Watch+Reserve share, peer percentile). This is the analytic core
of the Hack2Heal 2.0 idea "H1 Mirror". Round 1 evidence = the engine run unchanged on one month of England's
open English Prescribing Dataset (EPD), because India has no open prescription-level data.

## Ubiquitous language
- **Record**: one line = (prescriber, drug name, items). In India the source is a Schedule H1 register row; in the demo an EPD row.
- **AWaRe category**: Access | Watch | Reserve | Unclassified (drug not in WHO AWaRe 2023, e.g. anti-TB, methenamine).
- **Access share**: Access items / (Access + Watch + Reserve items) for one prescriber (Unclassified excluded).
- **Mirror**: a prescriber's Watch+Reserve share compared with the median of peers in the same area.

## Success criteria (numbers)
1. Coverage: ≥95% of antibacterial items in EPD June 2025 (BNF 5.1) receive an AWaRe category. (measured 97.3%)
2. Determinism: same input → same category; every category traceable to one row of the WHO table or one named override.
3. Speed: whole-country month (≈2.26M items, ≈7.9k organisations) aggregated + classified in < 60 s on a laptop. (measured ≈6 s)

## Given / When / Then
- Given "Co-amoxiclav (Amoxicillin/clavulanic acid)", When classified, Then Access (override → amoxicillin/clavulanic-acid).
- Given "Clarithromycin", Then Watch. Given "Linezolid", Then Reserve. Given "Colistimethate sodium", Then Reserve.
- Given "Methenamine hippurate" or "Isoniazid", Then Unclassified (not in AWaRe 2023).
- Given a prescriber with 80 Access and 20 Watch items, When mirrored against peers with median 16%, Then wr_share 0.20 and above-median flag true.

### v0.2 — Indian register / bill labels (2026-09-26)
- **Label**: one generic line as printed on an Indian pack or bill, e.g. "Ofloxacin 200mg & Ornidazole 500mg Tab".
- **Rule table**: WHO AWaRe 2023 (257 entries incl. listed combinations) + WHO "Not recommended" FDC sheet (103 rows → 101 after salt variants collapse). Source: `data/aware2023.json`, `data/notrec2023.json` (both from `WHO-MHP-HPS-EML-2023.04-eng.xlsx`).
- Given "Cefixime 200 mg Tablets IP", Then Watch. Given "Amoxycillin 500 mg + Potassium Clavulanate 125 mg Tablets", Then Access (Indian spelling + salt → WHO combination).
- Given "Cefixime 200 mg + Ofloxacin 200 mg Tablets" or "Ofloxacin 200mg & Ornidazole 500mg Tab", Then "Not recommended".
- Given any single EPD name, Then the label path returns the same category as `classify()` (v0.1 national run unchanged).
- Success: 5 label tests pass (`tests/test_labels.py`); v0.1 tests unchanged (4 pass).

### v0.3 — brand table, same-specialty mirror, privacy thresholds (2026-09-26, from the win-gate review)
- **Brand table**: brand → composition (`data/brandmap-gautham2022.json`, pairs as listed in Gautham 2022 Table 4); applied before the rule table.
- **Line**: (prescriber registration no. or None, specialty, pharmacy, category). **Denominator** = Access + Watch + Reserve lines of that
  prescriber from bills + H1 register (the H1 register alone holds mostly Watch drugs, so it can't be the denominator).
- Given "Taxim-O 200 Tablet", Then Watch; "Clavam 625", Then Access; an unknown brand, Then Unclassified (chemist maps it once).
- Given GPs and a chest physician, When mirrored, Then each is ranked only against the same specialty; < 20 lines → no letter;
  unregistered prescriber lines → never a letter.
- Given < 10 contributing pharmacies, When the district view is asked, Then None; otherwise aggregates with no pharmacy/prescriber ids.
- Success: 5 more tests (`tests/test_mirror.py`), total 14.

### v0.4 — route-split WHO entries, monthly use case, CLI, browser demo (2026-09-30)
- **Route**: WHO AWaRe 2023 lists 12 drugs per route (e.g. `minocycline_oral` Watch / `minocycline_iv` Reserve). The label's
  form word decides: Injection / Inj / Infusion / Vial → iv, otherwise oral.
- Given "Metronidazole 400 mg Tablets", Then Access. Given "Minocycline 100 mg Injection", Then Reserve; "… Capsules", Then Watch.
  Every route-split entry is reachable from a label (`tests/test_routes.py`, 2 tests).
- **Monthly mirror (application)**: register rows (date, pharmacy, prescriber_reg, specialty, drug_line, qty) → one rule table →
  letters (registered, ≥20 lines, same-specialty peers, WHO not-recommended combinations listed by name, top 3 Watch/Reserve lines)
  + district view (≥10 pharmacies) + unclassified labels to map once. Patient fields never enter the engine.
- Given R2 with 12 Access, 8 Watch, 3 not-recommended lines among 3 GPs, Then wr_share 0.40, above median, the combination is named.
- Given the synthetic sample month (`examples/register-sample.csv`, seed 20260930), Then 30 letters, district view of 12 pharmacies,
  "Zifi 200 Tablet" reported as unclassified (`tests/test_application.py`, 5 tests).
- CLI (`engine/cli.py`) writes 30 letters; the blind mock-register test re-scores to 40/40 verdicts, 35/40 reg. digits, 34/40 qty
  (`tests/test_cli_and_mock.py`, 2 tests). The browser demo (`index.html`) runs the same `domain/` + `application/` files in Pyodide.
- Success: 23 tests pass.

## Non-goals
Clinical appropriateness per patient (needs diagnosis); DDD-based metrics (EPD items only); handwriting extraction (Final Round).

## Layout
`domain/` pure rules (no I/O) ← `application/` (use cases; `run_evidence.py` for the national check) ← `adapters/`
(NHSBSA HTTP, register CSV, rule files, letter HTML) ← `cli.py` / `index.html` (infrastructure).
Tests: `python3 -m pytest -q engine/tests` (23 = v0.1 4 + v0.2 5 + v0.3 5 + v0.4 9).
