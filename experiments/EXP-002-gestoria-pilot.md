# EXP-002 — Gestoría invoice-to-ledger paid pilot

| field | value |
|---|---|
| ID | EXP-002 |
| Date | 2026-09-24 |
| Status | **READY, awaiting owner approval** (no outreach sent) |
| Hypothesis | A small Spanish gestoría will pay a €300 pilot, then €0.20 per accepted invoice, for supplier-invoice extraction into its accounting software, if field accuracy is ≥97% and staff only review exceptions. |
| Market | Spanish accounting firms (~60,000; 77% under 10 staff), per reports/cycle-01.md S1 |
| Customer | Gestoría owner, 2-10 staff, 30-150 business clients, on a3 / Sage / Contasol |
| Problem | Staff hours keying supplier invoices and fixing errors at quarter-end |
| Method | 25 qualified conversations → sample run on 20-50 of *their* invoices → report accuracy, review rate, cost → ask for the €300 pilot |
| Cost so far | €0 (build time only) |
| Budget | ≤ €20 API, ≤ 15 h of owner time |
| Result | — |
| Evidence | — |
| Failure reason | — |
| Next action | Owner: approve target list and script (`outreach/gestorias.md`); set `ANTHROPIC_API_KEY`; choose the province |

## Pass / kill (decided before starting)
- **PASS:** ≥2 paid pilots AND field-level accuracy ≥97% on their invoices AND human-review rate ≤10%.
- **KILL:** <2 paid pilots after 25 qualified conversations, OR accuracy <97% after two iteration rounds.
- **Pivot signal:** gestorías want it but only at a flat fee < €150/month. Contribution would then be ~18% (research/economics.md), so kill unless the review rate drops a lot.

## Funnel to record (in `ledger.json` → `money` and here)
| stage | count | date |
|---|---|---|
| contacted | 0 | |
| conversation held | 0 | |
| sample invoices received | 0 | |
| sample run delivered | 0 | |
| pilot offered | 0 | |
| pilot paid | 0 | |

## How to run a sample
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...          # never commit it
python -m invoice_pipeline.extract ./samples/<gestoria>/ ./runs/<gestoria>.jsonl
```
The command prints the unit economics: invoices, accepted, sent to human review, accepted by tier, model
cost, and **cost per accepted invoice**. Accuracy must be measured against the gestoría's own posted
entries, field by field. Record both.

## Data handling (required before touching real invoices)
- Sign a data-processing agreement (encargo de tratamiento) with the gestoría.
- Prefer anonymised or old invoices for the sample. Delete them after the report.
- `samples/` and `runs/` are git-ignored. Never commit customer documents.
