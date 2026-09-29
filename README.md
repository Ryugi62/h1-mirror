# H1 Mirror

**Schedule H1 register lines → a private monthly antibiotic mirror for every registered prescriber in India.**

[![tests](https://github.com/Ryugi62/h1-mirror/actions/workflows/tests.yml/badge.svg)](https://github.com/Ryugi62/h1-mirror/actions/workflows/tests.yml)
**Live demo (runs in your browser, nothing uploaded): https://ryugi62.github.io/h1-mirror/**

Since 2014 every Schedule H1 antibiotic sale in India must be written in a legal register (patient, prescriber, drug,
quantity, date; kept 3 years). Outside TB, those records are hardly read. In 2019, 54.9% of India's private-sector
antibiotic use (DDD) was WHO **Watch** and only 27.0% **Access** (Koya et al., 2022). H1 Mirror reads the lines chemists
already keep and gives each registered prescriber one private page a month: their Access / Watch / Reserve mix against
same-specialty peers, plus any WHO *not-recommended* combinations they prescribed. Peer-comparison letters cut
antibiotic items by 3.3% in a national RCT in England (Hallsworth et al., 2016); H1 Mirror adds that feedback loop to a
record India already mandates.

Idea submitted to **Hack2Heal 2.0 — Global Healthcare Innovation Hackathon** (Team Lumia, individual entry).

## What is built (and what is not yet)

| Part | Status | Where |
|---|---|---|
| Rule table: WHO AWaRe 2023 (257 entries, route-aware), 103 WHO not-recommended FDCs, Indian spellings, brand table | built, tested | `engine/domain/aware.py`, `engine/data/` |
| Monthly use case: lines → private letters (≥20 lines, same specialty) + district aggregate (≥10 pharmacies) | built, tested | `engine/application/monthly_mirror.py` |
| CSV adapter, printable HTML letter, CLI | built, tested | `engine/adapters/`, `engine/cli.py` |
| Chemist's own printable monthly register (their lines only, WHO group per line) | built, tested | `pharmacy_register` in `engine/application/` |
| Browser demo running the **same Python files** via Pyodide | built, checked headless | `index.html` |
| **Real Indian data check**: every marketed systemic antibiotic product in a public Indian medicine catalogue (253,973 products, MIT) classified; national brand table (59,341 brands) | reproducible | `engine/run_india_catalogue.py` → `engine/data/evidence-india-catalogue.json` |
| National-scale engine check: 2,264,718 NHS antibacterial items (June 2025), 97.3% classified | reproducible | `engine/run_evidence.py` → `engine/data/evidence-EPD_202506.json` |
| Blind mock-register reading test: 40 synthetic handwritten-style rows read by Claude Haiku | scored, reproducible | `mocktest/` |
| Photo capture app with on-phone patient masking | Final Round | — |
| Real (anonymised) register pages, Indian pilot | not yet — needs Indian partners | — |

The sample month in `examples/` is **synthetic** (seeded generator; no real pharmacy, prescriber or patient). The
England run is an engine check only; any effect in India has to be measured in India.

## Run it

```bash
python3 -m pip install pytest          # the engine itself is standard-library Python 3.9+
python3 -m pytest -q engine/tests      # 36 tests
python3 engine/cli.py examples/register-sample.csv --council examples/council-register-sample.txt --out out/   # letters in out/letters/, district view in out/district.json
python3 mocktest/score_mock.py mocktest/truth.json mocktest/predictions-haiku-2026-09-26.jsonl /tmp/mock.json
python3 engine/run_india_catalogue.py      # Indian catalogue check + national brand table (downloads the MIT catalogue, verifies sha256)
python3 engine/run_evidence.py EPD_202506   # national check (downloads aggregates from the NHSBSA open-data API)
```

Your own month: a CSV with `date, pharmacy, prescriber_reg, specialty, drug_line, qty[, source]`. Patient columns, if
present, are ignored. An empty `prescriber_reg` is an unregistered provider: counted in the district aggregate, never
sent a letter.

## What the number means (the metric)

- **Watch + Reserve share** of one prescriber = Watch + Reserve lines ÷ all WHO-classified antibiotic lines
  (Access + Watch + Reserve), counted **only from complete bill exports** (`source=bill`: every antibiotic line the
  billing software records, with the prescriber's registration number). The H1 register alone holds mostly Watch drugs,
  so photographed register rows (`source=h1_photo`) feed the district aggregate only, never a letter.
- A letter needs ≥20 such lines in the month and a registration number that is **on the council register list**
  (`--council`): a misread number never sends a letter to the wrong doctor. Specialty comes from the council register,
  not from the number.
- Peers = same specialty. Lines from unregistered providers and chemist-initiated sales without a prescription go to
  the district aggregate (≥10 pharmacies) only.
- Trial primary outcome: this share (lines); DDD-based share is secondary.

## Results so far

| Check | Result |
|---|---|
| Indian label lines → verdict (brands via Gautham et al. 2022) | Taxim-O 200 → Watch · Clavam 625 → Access · Cefixime + Ofloxacin → WHO not recommended · Linezolid → Reserve |
| **Indian medicine catalogue** (junioralive/Indian-Medicine-Dataset, MIT, 253,973 products) | 62,351 listed systemic antibiotic products (listed products, not sales) · **98.7% classified** · Watch 32,740 · Access 12,124 · Reserve 905 · **WHO not-recommended combinations 14,892 (23.9%)** · antibiotic combinations on neither WHO list 877 (named, not guessed) · unclassified 813 (mostly anti-TB) · 9 of 11 field-study brands (Gautham 2022) present · de-duplicated by (name, composition): 61,571 products, 98.7% / 24.1%. |
| **Accuracy audit** on 200 random catalogue products vs. an independent blind reader applying the same written WHO rules | **200/200 agree (Wilson 95% CI 98.1–100%)** — checks that the code implements the rules; clinical appropriateness is out of scope (`audit/`). |
| National-scale engine check (NHSBSA EPD, June 2025) | 2,264,718 items, 7,916 organisations, 97.3% classified, Access 83.6% of classified |
| Blind mock-register reading (40 synthetic rows, closed vocabulary of 16 drug lines, 5 handwriting-style fonts; Wilson 95% CI) | AWaRe verdict 40/40 (91–100%) · drug line + strength 40/40 · registration digits 35/40 (74–95%) · full reg. no. 31/40 (62–88%) · quantity 34/40 (71–93%) · **all fields right 27/40 (52–80%)**. Not real handwriting: real anonymised pages come next. |
| Synthetic sample month (12 pharmacies, 2 photo-only) | 1,466 lines · 22 letters · 143 photo lines and 11 misread-number lines kept out of letters · district Access 56.8% · 68 not-recommended lines · 1 unknown brand flagged to map |

## Classification rule (in order)

1. The exact ingredient set is on WHO's *not recommended* FDC list → **Not recommended**.
2. Exact WHO AWaRe 2023 entry (route from the form word for route-split drugs) → **Access / Watch / Reserve**.
3. Known non-antibiotic add-ons (probiotics, enzymes, mucolytics) are dropped and steps 1–2 re-run.
4. Two or more antibiotics on neither list → **Not WHO-listed combination**.
5. Anything unknown → **Unclassified** (never guessed; the chemist maps a new brand once).

## Design rules

- **Feedback, not enforcement**: no per-pharmacy report; the district sees aggregates of ≥10 pharmacies only.
- **Patterns, not verdicts**: same-specialty peers; Watch drugs are right for some patients; letters say so.
- **AI reads, rules decide**: a vision model may read a photo row, the chemist confirms it, and a fixed, auditable rule
  table assigns the group.
- **Privacy**: patient identity never enters the engine (masked on the phone in the capture app); only registered
  prescribers receive letters (DPDP Act 2023 consent and ethics approval before any pilot).

## Layout (clean architecture)

`engine/domain` (pure rules, no I/O) ← `engine/application` (use cases) ← `engine/adapters` (CSV, rule files, HTML
letter, NHSBSA API) ← `engine/cli.py` / `index.html`. Specification with Given/When/Then: [`engine/SPEC.md`](engine/SPEC.md).

## Sources and licences

- WHO AWaRe classification of antibiotics, 2023 (WHO-MHP-HPS-EML-2023.04), CC BY-NC-SA 3.0 IGO — `engine/data/aware2023.json`,
  `engine/data/notrec2023.json` are derived from it for non-commercial research use.
- Brand → composition pairs as listed in Gautham M et al., *Antibiotics* 2022;11(4):523, Table 4.
- Indian Medicine Dataset (junioralive, GitHub, MIT licence), `indian_medicine_data.csv`, sha256 `c9de0182…`, downloaded
  2026-09-29 — source of `engine/data/brandmap-india-catalogue.json`.
- NHS Business Services Authority, English Prescribing Dataset (Open Government Licence v3.0).
- Koya SF et al., *Lancet Reg Health SE Asia* 2022 · Hallsworth M et al., *Lancet* 2016 · Rakesh PS et al., *GHSP* 2021 ·
  Farooqui HH et al., *JAC-AMR* 2020 (full list of 16 references in the submission PDF).
- Code: MIT (see `LICENSE`). AI tools assisted with drafting and code; every number is computed by the engine or quoted
  from a cited source.
