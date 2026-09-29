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
| Browser demo running the **same Python files** via Pyodide | built, checked headless | `index.html` |
| National-scale engine check: 2,264,718 NHS antibacterial items (June 2025), 97.3% classified | reproducible | `engine/run_evidence.py` → `engine/data/evidence-EPD_202506.json` |
| Blind mock-register reading test: 40 synthetic handwritten-style rows read by Claude Haiku | scored, reproducible | `mocktest/` |
| Photo capture app with on-phone patient masking | Final Round | — |
| Real (anonymised) register pages, Indian pilot | not yet — needs Indian partners | — |

The sample month in `examples/` is **synthetic** (seeded generator; no real pharmacy, prescriber or patient). The
England run is an engine check only; any effect in India has to be measured in India.

## Run it

```bash
python3 -m pip install pytest          # the engine itself is standard-library Python 3.9+
python3 -m pytest -q engine/tests      # 23 tests
python3 engine/cli.py examples/register-sample.csv --out out/   # 30 letters in out/letters/, district view in out/district.json
python3 mocktest/score_mock.py mocktest/truth.json mocktest/predictions-haiku-2026-09-26.jsonl /tmp/mock.json
python3 engine/run_evidence.py EPD_202506   # national check (downloads aggregates from the NHSBSA open-data API)
```

Your own month: a CSV with `date, pharmacy, prescriber_reg, specialty, drug_line, qty`. Patient columns, if present, are
ignored. An empty `prescriber_reg` is an unregistered provider: counted in the district aggregate, never sent a letter.

## Results so far

| Check | Result |
|---|---|
| Indian label lines → verdict (brands via Gautham et al. 2022) | Taxim-O 200 → Watch · Clavam 625 → Access · Cefixime + Ofloxacin → WHO not recommended · Linezolid → Reserve |
| National-scale engine check (NHSBSA EPD, June 2025) | 2,264,718 items, 7,916 organisations, 97.3% classified, Access 83.6% of classified |
| Blind mock-register reading (40 rows, 5 handwriting fonts) | AWaRe verdict 40/40 · drug line + strength 40/40 · registration digits 35/40 · quantity 34/40 |
| Synthetic sample month (12 pharmacies) | 1,764 lines · 30 letters · district Access 63.9% · 57 not-recommended lines · 1 unknown brand flagged to map |

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
- NHS Business Services Authority, English Prescribing Dataset (Open Government Licence v3.0).
- Koya SF et al., *Lancet Reg Health SE Asia* 2022 · Hallsworth M et al., *Lancet* 2016 · Rakesh PS et al., *GHSP* 2021 ·
  Farooqui HH et al., *JAC-AMR* 2020 (full list of 16 references in the submission PDF).
- Code: MIT (see `LICENSE`). AI tools assisted with drafting and code; every number is computed by the engine or quoted
  from a cited source.
