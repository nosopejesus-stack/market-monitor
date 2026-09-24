# XAUUSD — Cycle 02 verification & red team (generated tables)


## V1 — Data integrity

- Trading days used: **1722** (Mon-Fri MT5 server days, NY 17:00 boundary). Weekend server days excluded: 132 (2517 H1 bars, median range $0.28 vs $4.91 on weekdays). These are provider quotes outside broker hours (present only from April 2025) and are excluded from both signals and trade management.
- Weekday days dropped for having <10 bars: ['2020-01-24', '2023-04-07'].
- H1 bars per trading day: median 23.0, min 12.0. Largest gap inside a trading day: 12 h.


## V2 — Look-ahead audit (programmatic)

- Every fill happens at or after 17:00 NY of the signal day (candle fully closed): **True**
- Every fill happens on the next trading day only (order expiry respected): **True**
- Features recomputed on data truncated at day t equal the full-sample features at t: **40/40** random days match
- The signal uses only the close and open of day t; order levels use only close_t. Tercile cut points in cycle 01 were fitted on 2020-2022 only.


## V3 — Independent re-implementation

`xau/independent.py` re-implements the literal rule in plain Python from the rule text, sharing no simulation code.

| implementation | fills | win_rate | mean_R |
|---|---|---|---|
| engine.py (numba) | 599 | 0.688 | -0.020 |
| independent.py | 599 | 0.688 | -0.020 |

Trade-by-trade outcome agreement: **100.00%** of 921 signals; max P&L difference on common closed trades: $0.0000.


## V4 — Intrabar calibration with M5 bars (2026-01-02 → 2026-09-23)

M5 aggregated to hours reproduces H1 exactly on every complete hour (median |diff| $0.000), so H1 contains no spurious spikes. The M5 download has gaps at chunk joins, so only the 60 bullish signals whose next 3 trading days have complete M5 coverage are compared.

| bars | mode | fills | win_rate | mean_R | t |
|---|---|---|---|---|---|
| H1 | worst | 47 | 0.383 | -0.449 | -4.358 |
| H1 | path | 47 | 0.723 | 0.040 | 0.425 |
| H1 | best | 47 | 0.723 | 0.040 | 0.425 |
| M5 | worst | 47 | 0.596 | -0.143 | -1.376 |
| M5 | path | 47 | 0.681 | -0.021 | -0.210 |
| M5 | best | 47 | 0.681 | -0.021 | -0.210 |

H1-PATH vs M5-PATH outcome agreement on trades closed in both: **95.7%**. Signals whose outcome depends on intrabar order: H1 26.7% → M5 6.7%. 2026 is the most volatile year in the sample (median ATR ≈ $106), so this is a worst case for H1 ambiguity.


## V5 — Daily-candle definition sensitivity (PATH, $0.30)

| day_definition | signals | fills | win_rate | mean_R | ci95 | t |
|---|---|---|---|---|---|---|
| NY 17:00 (MT5 standard) | 921 | 599 | 0.688 | -0.020 | [-0.075, 0.032] | -0.716 |
| UTC 00:00 | 917 | 589 | 0.671 | -0.078 | [-0.140, -0.023] | -2.533 |
| NY 17:00, drop 17:00-18:00 NY bars | 925 | 600 | 0.688 | -0.019 | [-0.074, 0.032] | -0.676 |



## V6 — Realistic transaction costs

Holding time: median 0 rollovers, mean 0.32; 80% of trades close before the first rollover. Commission $0.07/oz ≈ $7 per 100-oz lot (raw-spread broker, ASSUMPTION); FTMO reportedly charges none on metals (secondary source). Swap values are sensitivity bounds, not your broker's rates.

| spread | commission_$/oz | swap_$/oz/night | fills | mean_R | t | total_R |
|---|---|---|---|---|---|---|
| 0.150 | 0.000 | -0.600 | 597 | -0.029 | -1.046 | -17.192 |
| 0.150 | 0.000 | 0.000 | 597 | -0.017 | -0.628 | -10.248 |
| 0.150 | 0.000 | 0.300 | 597 | -0.011 | -0.416 | -6.777 |
| 0.150 | 0.070 | -0.600 | 597 | -0.033 | -1.204 | -19.778 |
| 0.150 | 0.070 | 0.000 | 597 | -0.021 | -0.786 | -12.835 |
| 0.150 | 0.070 | 0.300 | 597 | -0.016 | -0.575 | -9.363 |
| 0.300 | 0.000 | -0.600 | 599 | -0.031 | -1.137 | -18.779 |
| 0.300 | 0.000 | 0.000 | 599 | -0.020 | -0.716 | -11.762 |
| 0.300 | 0.000 | 0.300 | 599 | -0.014 | -0.504 | -8.253 |
| 0.300 | 0.070 | -0.600 | 599 | -0.036 | -1.295 | -21.374 |
| 0.300 | 0.070 | 0.000 | 599 | -0.024 | -0.874 | -14.357 |
| 0.300 | 0.070 | 0.300 | 599 | -0.018 | -0.662 | -10.848 |
| 0.500 | 0.000 | -0.600 | 604 | -0.044 | -1.603 | -26.767 |
| 0.500 | 0.000 | 0.000 | 604 | -0.033 | -1.189 | -19.750 |
| 0.500 | 0.000 | 0.300 | 604 | -0.027 | -0.980 | -16.241 |
| 0.500 | 0.070 | -0.600 | 604 | -0.049 | -1.760 | -29.383 |
| 0.500 | 0.070 | 0.000 | 604 | -0.037 | -1.346 | -22.366 |
| 0.500 | 0.070 | 0.300 | 604 | -0.031 | -1.137 | -18.857 |



## V7 — Randomised controls and the geometry null

| control | mean_R | win_rate | range_5_95 |
|---|---|---|---|
| observed rule (bullish days, SELL STOP) | -0.020 | 0.688 |  |
| 5,000 random same-size subsets of all filled days | -0.045 |  | [-0.076, -0.014] |
| 2,000 coin-flip directions on the same bullish days | -0.027 |  | [-0.059, 0.004] |
| 40 synthetic driftless random walks (shuffled H1 returns), same rule and spread | -0.011 | 0.688 | [-0.043, 0.036] |

Random-subset two-sided p = 0.171. Synthetic random walks produce a 68.8% win rate (5-95%: 66.6%-72.0%) with the same rule: the win rate is a property of the TP/SL geometry and the spread, not of gold.


## V8 — Parameter perturbation around 708/708/1616 (125 combinations, PATH, $0.30)

- Share of combinations with mean R > 0: **19%**; with t > 2: **0%**
- Mean R across the neighbourhood: median -0.027, range -0.082 … +0.025
- Best of 125 by t (a multiple-testing artefact until shown otherwise): offset 900, tp 708, sl 1400, mean R +0.025, t 0.83. With 125 tries, the expected maximum t under pure noise is about 2.4-2.6.

| sl | mean_R | share_positive |
|---|---|---|
| 1200 | -0.020 | 0.480 |
| 1400 | -0.019 | 0.400 |
| 1616 | -0.029 | 0.080 |
| 1800 | -0.037 | 0.000 |
| 2000 | -0.038 | 0.000 |



## V9 — Walk-forward (re-optimise on the prior 2 years, trade the next year)

| test_year | chosen_on_prior_2y | IS_mean_R | OOS_mean_R | OOS_fills | literal_mean_R |
|---|---|---|---|---|---|
| 2022 | 900/600/1400 | 0.033 | 0.091 | 72 | 0.136 |
| 2023 | 708/900/1200 | 0.082 | -0.076 | 77 | -0.092 |
| 2024 | 600/600/1616 | 0.049 | -0.104 | 96 | 0.003 |
| 2025 | 800/900/1800 | 0.047 | -0.117 | 110 | -0.114 |
| 2026 | 800/800/1200 | 0.005 | 0.208 | 80 | 0.118 |

Concatenated walk-forward OOS: mean R **-0.013** (t -0.36) vs literal +0.002 on the same years. In-sample winners do not carry forward.


## V10 — Periods and regimes (literal, PATH, $0.30)

| segment | fills | win_rate | mean_R | ci95 | t |
|---|---|---|---|---|---|
| 2020-2021 | 160 | 0.637 | -0.078 | [-0.189, 0.028] | -1.391 |
| 2022-2023 | 158 | 0.715 | 0.025 | [-0.077, 0.125] | 0.484 |
| 2024-2026 | 281 | 0.701 | -0.012 | [-0.090, 0.065] | -0.297 |
| uptrend | 376 | 0.694 | -0.013 | [-0.079, 0.051] | -0.391 |
| downtrend | 94 | 0.691 | -0.006 | [-0.144, 0.117] | -0.092 |
| no trend | 129 | 0.667 | -0.047 | [-0.164, 0.070] | -0.786 |
| ATR < $30 | 277 | 0.675 | -0.026 | [-0.109, 0.052] | -0.645 |
| ATR $30-60 | 192 | 0.688 | -0.022 | [-0.114, 0.075] | -0.448 |
| ATR ≥ $60 | 127 | 0.717 | -0.002 | [-0.115, 0.112] | -0.027 |



## V11 — Survivability (prop-firm style limits)

Maximum simultaneous open positions in history: **2** (each at full risk). Block bootstrap (blocks of 10 trades) keeps losing streaks.

| risk_per_trade | trades_per_year | P(max_DD>=10%) block-bootstrap | median_1y_return | P(1y>0) | worst_actual_day | days_worse_than_-5% |
|---|---|---|---|---|---|---|
| 0.005 | 90 | 0.009 | -0.009 | 0.390 | -0.010 | 0 |
| 0.010 | 90 | 0.278 | -0.015 | 0.412 | -0.020 | 0 |



## V12 — What '708 points' means changes the trade, not the verdict

| reading | tp_$ | fills | win_rate | mean_R | ci95 | t |
|---|---|---|---|---|---|---|
| 1 pt = $0.001 (3-digit feed) | 0.708 | 882 | 0.688 | -0.212 | [-0.301, -0.130] | -4.964 |
| 1 pt = $0.01 (2-digit MT5, primary) | 7.080 | 599 | 0.688 | -0.020 | [-0.076, 0.033] | -0.716 |
| 1 pt = $0.10 ('pips') | 70.800 | 53 | 0.706 | 0.012 | [-0.170, 0.172] | 0.137 |

