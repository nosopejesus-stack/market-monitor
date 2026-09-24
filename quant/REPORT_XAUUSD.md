# EXP-001 — XAUUSD "SELL STOP after bullish daily close": falsification report

**Verdict: REJECTED as specified.** The literal rule shows no edge. Its 68.8% win rate is what a
coin-flip random walk produces with these TP/SL distances (69.5%). After a realistic spread, the
expectancy is slightly negative and statistically indistinguishable from zero. Do not trade it with real
or prop-firm capital.

All numbers below are produced by `python -m xau.study` (run from `quant/`) and are reproduced in full in
[`results/xau_study.md`](results/xau_study.md). Nothing was typed by hand.

## 1. Hypothesis as tested

| item | value |
|---|---|
| Instrument | XAU/USD spot (Twelve Data) |
| Signal | daily candle closes bullish (close > open), MT5 server day = NY 17:00 → 17:00 |
| Order | SELL STOP at previous close − 708 points, placed at the close |
| TP / SL | 708 / 1616 points from entry |
| Point | **ASSUMPTION** 1 point = $0.01 (MT5 2-digit XAUUSD) → $7.08 / $7.08 / $16.16 |
| Order life | next trading day only (unfilled orders cancelled) |
| Exit | TP or SL only, no time exit |
| Costs | spread modelled as half-spread on every trigger, base **$0.30** (ASSUMPTION), sensitivity 0 → $1.00 |
| R | 1R = SL distance ($16.16) |

**Structural fact to understand first.** With TP 708 and SL 1616, a driftless random walk hits TP first
1616 / (708 + 1616) = **69.5%** of the time, with zero expectancy. A ~70% win rate is automatic and says
nothing about edge. The only question is whether the rule beats 69.5% after costs.

## 2. Data

| dataset | coverage | use |
|---|---|---|
| H1 bars | 2020-01-24 → 2026-09-24, 39,614 bars in 1,722 trading days | main test; intrabar sequencing |
| Native D1 bars | 2006-01-03 → 2019-12-31, 3,639 days | independent era, bounds only |
| Native D1 bars | 1995-2005 | **discarded**: median daily range $0.75-2.50, i.e. fixing prices, not OHLC |

Data-quality findings:
- The H1 timestamps are **Australia/Sydney** local time. The daily maintenance gap lands at 07:00, 08:00 or 09:00 local depending on US and Australian DST, which is always 17:00 New York. Daily bars were rebuilt from H1 on the NY-17:00 boundary to match MT5/FTMO server days.
- Native D1 bars from 2024 on contain Saturday stubs, excluded.
- Gold's median daily ATR went from ~$23 (2021-23) to $51 (2025) and **$106 (2026)**. A fixed $7.08 offset means something very different in 2026 than in 2021.

## 3. Results

### 3.1 Literal rule (H1, 2020-2026)

| spread | intrabar mode | fills | win rate | mean R | 95% CI | t |
|---|---|---|---|---|---|---|
| $0.00 | PATH | 593 | 69.6% | −0.008 | [−0.061, +0.044] | −0.29 |
| $0.30 | WORST (lower bound) | 599 | 61.1% | −0.130 | [−0.186, −0.076] | −4.52 |
| $0.30 | PATH (best estimate) | 599 | 68.8% | −0.020 | [−0.076, +0.034] | −0.72 |
| $0.30 | BEST (upper bound) | 599 | 68.9% | −0.017 | [−0.071, +0.036] | −0.63 |
| $1.00 | PATH | 613 | 65.9% | −0.061 | [−0.117, −0.010] | −2.21 |

- 7.8% of fills touch both TP and SL inside one H1 bar. WORST/BEST bound the truth, and even the upper bound is negative.
- About 90 trades a year, with a max drawdown of 22R in PATH mode.

### 3.2 Controls: does the bullish-close condition add anything?

| test | fills | win rate | mean R | t |
|---|---|---|---|---|
| **bullish → SELL STOP (hypothesis)** | 599 | 68.8% | −0.020 | −0.72 |
| every day → SELL STOP | 1,125 | 67.0% | −0.045 | −2.23 |
| bearish → SELL STOP | 526 | 65.0% | −0.074 | −2.47 |
| bullish → BUY STOP (mirror) | 660 | 68.0% | −0.036 | −1.35 |

Permutation test against random same-size day subsets: p = 0.18. Short gold has fought a strong bull
trend ($1,582 → $4,293 over the sample), and the condition only makes a losing order "less bad". That is not an edge.

### 3.3 Stability

The strategy was positive in 2 of 7 years (2022 +0.14R, 2026 +0.12R) and negative or flat in the other 5.
IS 2020-22: −0.006R. OOS 2023-26: −0.029R.

### 3.4 Conditional slices (44 tested)

Tercile cut points were fixed on 2020-22 only. Benjamini-Hochberg correction was applied across all 44
slices. What was tested: 1, 2 or 3+ consecutive bullish candles; "two large bullish recovery candles";
body, upper-wick and lower-wick size; close location; volatility regime; ATR level; trend and range
regime; distance to 20-day high/low; weekday; NFP-day proxy; and fill session.

Only one slice survives FDR correction (q < 0.05): **large bullish bodies (≥ 0.53 ATR) are bad for this
short**, at −0.134R (IS −0.149, OOS −0.126). That makes sense as momentum: after a strong up day,
selling a pullback gets run over.

"Pick the best 5 on IS, check OOS" (T5) shows the usual decay. The best IS slice, mid volatility
(+0.186R, t 2.5), falls to −0.024R out of sample.

### 3.5 Parameter robustness

With geometry scaled to ATR (offset = TP = k·ATR, SL/TP ∈ {1.5, 2.28, 3}):
- Only k ≈ 0.3–0.5 gives a positive "bullish minus every-day" difference (+0.04 to +0.06R).
- Absolute expectancy is ~0 at best (+0.022R, t 0.77) and negative elsewhere.
- The ×10 reading of "points" ($70.80 / $161.60) gives only 53 fills in 6.7 years: +0.012R, t 0.14. No evidence either way.

### 3.6 Independent era (2006-2019, daily bars only)

Daily bars can't order intraday events, so only bounds are available:
- **Literal rule:** from −0.182R (WORST) to −0.013R (BEST). Not positive even under the most favourable assumption.
- **The two post-hoc filters** were re-tested here, where they were *not* discovered:
  - "Body < 0.53 ATR" vs "≥ 0.53 ATR" **replicates as a relative effect** (permutation p ≤ 0.002 under both bounds). The absolute range is −0.116R to +0.043R, so an edge is not established.
  - "3+ consecutive bullish" **does not replicate** (p = 0.53–0.90). Killed.

### 3.7 Monte Carlo (prop-firm framing)

Bootstrap of 90 trades per year from the literal-rule distribution:

| risk/trade | median 1-yr | P(1-yr > 0) | P(max DD ≥ 5%) | P(max DD ≥ 10%) |
|---|---|---|---|---|
| 0.5% | −0.8% | 40% | 27% | 0.8% |
| 1.0% | −1.6% | 40% | 80% | 27% |

At 1% risk, roughly one year in four would breach a 10% max-loss rule, with a negative median.

## 4. What survives and what to do

| item | status | next action |
|---|---|---|
| Literal rule | **KILLED** | none |
| ×10 points reading | inconclusive (53 fills) | only worth revisiting if you confirm this is what you meant |
| "3+ bullish candles" filter | **KILLED** (failed out of era) | none |
| "Skip bullish bodies ≥ 0.53 ATR" | **relative effect replicated, absolute edge unproven** | optional: pre-registered paper-trade for 6 months, stop if mean R < 0 after 60 fills; do not allocate capital |

Even if the filtered variant were real at +0.05R per trade, with ~55 fills a year at 0.5% risk it
would earn about 1.4% a year. The economic value is low, and the time is better spent on the business
experiments.

## 5. Limitations (read before trusting anything)

- Twelve Data spot is a composite feed. Broker prices, spreads and weekend gaps differ. The $0.30 spread is an assumption.
- There is no intrabar data before 2020, so the 2006-2019 test is bounds-only.
- The fill-session and NFP slices are coarse proxies; there was no news calendar.
- The fixed-dollar geometry makes results depend on the volatility regime, which the ATR test shows.
- The 44 slices plus 18 geometries plus controls are about 70 hypotheses. Anything with p ≈ 0.05 is expected noise.

## 6. Red-team note on the existing `market_monitor_v1` scoring

The daily email's directional "score" combines:
- **Monte Carlo from a GBM** fitted on the last 6 months. For a 1-day horizon, `prob_up` ≈ Φ(μ/σ), which barely differs from 50%. It encodes the sign of recent drift and carries no forward information.
- **TextBlob polarity of headlines**, a generic lexicon not trained on financial text.

No backtest supports either component. Until one does, treat the email as a calendar and volatility
brief, not a directional signal.
