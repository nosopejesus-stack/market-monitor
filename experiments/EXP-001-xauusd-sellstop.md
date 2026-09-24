# EXP-001 — XAUUSD SELL STOP after bullish daily close

| field | value |
|---|---|
| ID | EXP-001 |
| Date | 2026-09-24 |
| Status | **KILLED** |
| Hypothesis | After a bullish daily close, a SELL STOP 708 points below the close with TP 708 / SL 1616 has positive expectancy |
| Market | XAUUSD, own / prop-firm capital |
| Customer | self |
| Problem | find a tradable edge |
| Method | Event backtest on H1 2020-2026 (MT5 NY-17:00 days) with WORST/PATH/BEST intrabar bounds; controls (every day, bearish, mirror BUY STOP, permutation); 44 slices with IS-only cut points and BH-FDR; IS→OOS selection; ATR-scaled geometry grid; D1 2006-2019 independent era; bootstrap Monte Carlo |
| Cost | ~60 Twelve Data credits (existing free plan); engineering time |
| Result | 599 trades, WR 68.8% vs 69.5% random-walk breakeven, **−0.020R/trade** (95% CI −0.076…+0.034) at $0.30 spread; IS −0.006R, OOS −0.029R; 2006-2019 bounds −0.182R…−0.013R |
| Evidence | `quant/REPORT_XAUUSD.md`, `quant/results/xau_study.md`, `quant/results/xau_study.json` |
| Failure reason | The high win rate is the one TP/SL geometry implies for a random walk. Short entries fought a bull market ($1,582 → $4,293). |
| Next action | No capital. Optional pre-registered paper test of "skip bullish bodies ≥ 0.53 ATR" (stop after 60 fills if mean R < 0). Owner to confirm broker point size. |

Reproduce:
```bash
cd quant && python -m xau.study
```
