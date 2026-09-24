# Money Engine

Evidence-first lab for finding, testing and killing money-making opportunities.
Primary metric: **economic value created**, not code.

**Start here:** [`reports/cycle-03.md`](reports/cycle-03.md) (revenue-first cycle, in Spanish: top 5, selected experiment
EXP-006 "memoria técnica exprés", and the exact next human action). Earlier: [`cycle-02`](reports/cycle-02.md)
(XAUUSD **ARCHIVED — NO EDGE**, invoices **NO-GO — FROZEN**), [`cycle-01`](reports/cycle-01.md) · dashboard: `python dashboard/build_dashboard.py`, then open `dashboard/index.html`.

| path | what |
|---|---|
| `reports/` | cycle reports (opportunities, fast-cash, compounding, quant, first experiment, sources) |
| `research/` | 102-item opportunity longlist with kill reasons, scoring, scenario economics (scripts + outputs) |
| `experiments/` | experiment ledger (`ledger.json` = source of truth) and one file per experiment |
| `dashboard/` | money dashboard generated from the ledger. ACTUAL, ESTIMATE and ASSUMPTION are always labelled. |
| `quant/` | XAUUSD event backtester, falsification study (cycle 01), independent re-implementation and verification/red team (cycle 02). EXP-001: NO EDGE |
| `invoice_pipeline/` | Spanish supplier-invoice extraction (Haiku → Opus → human), deterministic NIF/VAT/total validation, tax-regime routing, duplicate detection, ground-truth evaluator. EXP-002 is NO-GO; kept as a tested component |
| `tender_agent/` | EXP-006: PLACSP discovery (open tenders × local past winners), pliego analysis + memoria drafting agent, deterministic QA (envelope contamination, coverage, page limits), ROI and job economics, demo, delivery workflow |
| `prospects/` | public-data prospect lists, all NOT CONTACTED |
| `energy_audit/` | S2 MVP: contracted-power audit (deterministic, uses the customer's own invoice prices) |
| `landing/`, `outreach/` | go-to-market drafts (EXP-002 superseded; EXP-006 `outreach/memorias.md`). **Nothing published or sent.** |
| `market_monitor_v1/` | the original daily-email market monitor, unpacked from `market-monitor.zip`. Its GitHub workflows are inside the subfolder, so they do **not** run. Move `.github/` to the repo root only if you want them active. |

## Setup and tests
```bash
pip install -r requirements.txt
python -m pytest -q quant/tests energy_audit/tests invoice_pipeline/tests tender_agent/tests
python -m tender_agent.qa tender_agent/demo/memoria_borrador.md tender_agent/demo/criterios.json
cd quant && python -m xau.study && python -m xau.verify   # regenerates quant/results/*
python research/pilot_economics.py > research/pilot_economics.md
python -m energy_audit.optimizer energy_audit/examples/synthetic_restaurant.json
```

## Rules this repo follows
- No fabricated customers, revenue, prices or backtests. Unknowns are marked UNVERIFIED.
- No real-money trading and no outward action (emails, publishing, payments) without explicit human approval.
- Secrets only via environment variables (`ANTHROPIC_API_KEY`). Customer documents never go in git (`samples/` and `runs/` are ignored).
- Deterministic code for anything checkable; models only where reading or reasoning is needed.
