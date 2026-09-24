# Money Engine

Evidence-first lab for finding, testing and killing money-making opportunities.
Primary metric: **economic value created**, not code.

**Start here:** [`reports/cycle-01.md`](reports/cycle-01.md) (research, 14 surviving opportunities,
economics, first experiment) · dashboard: `python dashboard/build_dashboard.py`, then open `dashboard/index.html`.

| path | what |
|---|---|
| `reports/` | cycle reports (opportunities, fast-cash, compounding, quant, first experiment, sources) |
| `research/` | 102-item opportunity longlist with kill reasons, scoring, scenario economics (scripts + outputs) |
| `experiments/` | experiment ledger (`ledger.json` = source of truth) and one file per experiment |
| `dashboard/` | money dashboard generated from the ledger. ACTUAL, ESTIMATE and ASSUMPTION are always labelled. |
| `quant/` | XAUUSD data, event backtester, falsification study, report (EXP-001, killed) |
| `invoice_pipeline/` | S1 MVP: Spanish supplier-invoice extraction. Haiku → Opus → human routing, deterministic NIF/VAT validation, cost per accepted invoice. |
| `energy_audit/` | S2 MVP: contracted-power audit (deterministic, uses the customer's own invoice prices) |
| `landing/`, `outreach/` | EXP-002 go-to-market drafts. **Not published or sent.** |
| `market_monitor_v1/` | the original daily-email market monitor, unpacked from `market-monitor.zip`. Its GitHub workflows are inside the subfolder, so they do **not** run. Move `.github/` to the repo root only if you want them active. |

## Setup and tests
```bash
pip install -r requirements.txt
python -m pytest -q quant/tests energy_audit/tests invoice_pipeline/tests
cd quant && python -m xau.study          # regenerates quant/results/*
python research/economics.py > research/economics.md
python -m energy_audit.optimizer energy_audit/examples/synthetic_restaurant.json
```

## Rules this repo follows
- No fabricated customers, revenue, prices or backtests. Unknowns are marked UNVERIFIED.
- No real-money trading and no outward action (emails, publishing, payments) without explicit human approval.
- Secrets only via environment variables (`ANTHROPIC_API_KEY`). Customer documents never go in git (`samples/` and `runs/` are ignored).
- Deterministic code for anything checkable; models only where reading or reasoning is needed.
