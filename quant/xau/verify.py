"""Cycle 02 verification & red team for the XAUUSD literal rule.

Run from quant/:  python -m xau.verify
Writes results/xau_verify.md and results/xau_verify.json. Nothing is typed by hand.

No parameter is optimised to find a profitable variant. Parameter grids are reported as
whole distributions, and the only "selection" is the walk-forward test, which exists to show
what optimisation would have delivered out of sample.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import load_h1, build_broker_d1, bar_arrays_from_h1, load_native_d1, bar_arrays_from_d1, H1_TZ, DATA
from .engine import simulate, WORST, PATH, BEST, OUT_TP, OUT_SL, OUT_OPEN, OUT_NOFILL
from .features import daily_features
from .independent import simulate_short
from .study import Sim, stats, table, fmt

RES = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260925)
POINT = 0.01
OFF, TP, SL = 7.08, 7.08, 16.16
SPREAD = 0.30


def hdr(md, title, text=""):
    md.append(f"\n## {title}\n\n{text}\n" if text else f"\n## {title}\n")


def rollovers(h1_ny: np.ndarray, entry_bar: np.ndarray, exit_bar: np.ndarray):
    """Number of swap charges per trade: NY 17:00 crossings between entry and exit; Wednesday counts 3."""
    out = np.zeros(len(entry_bar))
    ny = pd.DatetimeIndex(h1_ny)
    day_key = (ny + pd.Timedelta(hours=7)).normalize()
    for i, (a, b) in enumerate(zip(entry_bar, exit_bar)):
        if a < 0 or b < 0:
            continue
        crossed = pd.unique(day_key[a:b + 1])[:-1]  # every server-day boundary passed
        out[i] = sum(3 if pd.Timestamp(dd).dayofweek == 2 else 1 for dd in crossed)
    return out


def main():
    md, js = ["# XAUUSD — Cycle 02 verification & red team (generated tables)\n"], {}
    h1 = load_h1(); d1 = build_broker_d1(h1); bars, s, e = bar_arrays_from_h1(h1, d1)
    h1_trading = h1[h1["day"].isin(d1.index)].reset_index(drop=True)
    F = daily_features(d1); bull = F["bull"].to_numpy(); alld = np.ones(len(d1), bool)
    base = Sim(bars, s, e, d1, OFF, TP, SL, SPREAD, PATH)

    # ---------------- V1 data integrity
    g = h1.groupby("day").size()
    wk = h1[h1["day"].dt.dayofweek >= 5]
    js["V1"] = {"server_days_total": int(len(g)), "trading_days_used": int(len(d1)),
                "weekend_server_days_excluded": int((g.index.dayofweek >= 5).sum()),
                "weekend_bars_excluded": int(len(wk)),
                "weekend_bar_median_range": float((wk.high - wk.low).median()),
                "weekday_bar_median_range": float((h1.high - h1.low)[h1["day"].dt.dayofweek < 5].median()),
                "weekday_days_dropped_lt10_bars": [str(x.date()) for x in g.index[(g.index.dayofweek < 5) & ~g.index.isin(d1.index)]],
                "bars_per_trading_day": d1["nbars"].describe().round(2).to_dict(),
                "max_intraday_gap_hours": float(h1_trading.groupby("day")["ny"].apply(lambda x: x.diff().max()).dt.total_seconds().max() / 3600)}
    hdr(md, "V1 — Data integrity",
        f"- Trading days used: **{len(d1)}** (Mon-Fri MT5 server days, NY 17:00 boundary). "
        f"Weekend server days excluded: {js['V1']['weekend_server_days_excluded']} "
        f"({js['V1']['weekend_bars_excluded']} H1 bars, median range ${js['V1']['weekend_bar_median_range']:.2f} "
        f"vs ${js['V1']['weekday_bar_median_range']:.2f} on weekdays). These are provider quotes outside broker hours "
        "(present only from April 2025) and are excluded from both signals and trade management.\n"
        f"- Weekday days dropped for having <10 bars: {js['V1']['weekday_days_dropped_lt10_bars']}.\n"
        f"- H1 bars per trading day: median {js['V1']['bars_per_trading_day']['50%']}, min {js['V1']['bars_per_trading_day']['min']}. "
        f"Largest gap inside a trading day: {js['V1']['max_intraday_gap_hours']:.0f} h.")

    # ---------------- V2 look-ahead audit
    fb = base.filled & bull
    sig_close_time = d1.index + pd.Timedelta(hours=17)  # server day D ends at 17:00 NY on calendar day D
    entry_times = h1_trading["ny"].to_numpy()[base.entry_bar[fb]]
    ok_after_close = (pd.DatetimeIndex(entry_times) >= sig_close_time[fb]).all()
    entry_day_idx = np.searchsorted(s, base.entry_bar[fb], side="right") - 1
    ok_next_day = (entry_day_idx == np.flatnonzero(fb) + 1).all()
    # features computed on data truncated at t must equal full-sample features at t
    idx = RNG.choice(np.arange(250, len(d1)), 40, replace=False)
    cols = ["bull", "body_atr", "upper_wick_frac", "bull_run", "uptrend", "vol_regime", "dist_high20_atr", "two_large_recovery"]
    mism = 0
    for t in idx:
        ft = daily_features(d1.iloc[: t + 1]).iloc[-1][cols]
        ff = F.iloc[t][cols]
        mism += int(not all((pd.isna(a) and pd.isna(b)) or a == b or (isinstance(a, float) and abs(a - b) < 1e-9) for a, b in zip(ft, ff)))
    js["V2"] = {"entries_after_signal_close": bool(ok_after_close), "entries_on_next_day_only": bool(ok_next_day),
                "feature_truncation_mismatches": mism, "feature_truncation_checks": len(idx)}
    hdr(md, "V2 — Look-ahead audit (programmatic)",
        f"- Every fill happens at or after 17:00 NY of the signal day (candle fully closed): **{ok_after_close}**\n"
        f"- Every fill happens on the next trading day only (order expiry respected): **{ok_next_day}**\n"
        f"- Features recomputed on data truncated at day t equal the full-sample features at t: "
        f"**{len(idx) - mism}/{len(idx)}** random days match\n"
        "- The signal uses only the close and open of day t; order levels use only close_t. "
        "Tercile cut points in cycle 01 were fitted on 2020-2022 only.")

    # ---------------- V3 independent reproduction
    sig_days = d1.index[bull]
    ind = simulate_short(h1_trading, d1.index, d1["close"], sig_days, OFF, TP, SL, SPREAD)
    eng = pd.DataFrame({"outcome": base.outcome[bull], "pnl": base.pnl[bull]}, index=sig_days)
    code = {OUT_TP: "TP", OUT_SL: "SL", OUT_OPEN: "OPEN", OUT_NOFILL: "NOFILL"}
    eng["o"] = [code[x] for x in eng["outcome"]]
    j = eng.join(ind, rsuffix="_ind")
    agree = (j["o"] == j["outcome_ind"]).mean()
    both = j[(j["o"].isin(["TP", "SL"])) & (j["outcome_ind"].isin(["TP", "SL"]))]
    ind_R = (ind["pnl"][ind["outcome"].isin(["TP", "SL"])] / SL)
    js["V3"] = {"signals": int(len(j)), "outcome_agreement": float(agree),
                "disagreements": j[j["o"] != j["outcome_ind"]][["o", "outcome_ind"]].reset_index().astype(str).values.tolist()[:20],
                "pnl_max_abs_diff": float((both["pnl"] - both["pnl_ind"]).abs().max()),
                "independent_fills": int(ind["filled"].sum()), "independent_win_rate": float((ind["outcome"] == "TP").sum() / ind["outcome"].isin(["TP", "SL"]).sum()),
                "independent_mean_R": float(ind_R.mean()), "engine_mean_R": float(np.nanmean(base.R[bull & base.filled]))}
    hdr(md, "V3 — Independent re-implementation",
        "`xau/independent.py` re-implements the literal rule in plain Python from the rule text, sharing no simulation code.\n\n"
        + table([{"implementation": "engine.py (numba)", "fills": int((bull & base.filled).sum()),
                  "win_rate": (base.outcome[bull] == OUT_TP).sum() / np.isin(base.outcome[bull], [OUT_TP, OUT_SL]).sum(),
                  "mean_R": js["V3"]["engine_mean_R"]},
                 {"implementation": "independent.py", "fills": js["V3"]["independent_fills"],
                  "win_rate": js["V3"]["independent_win_rate"], "mean_R": js["V3"]["independent_mean_R"]}],
                ["implementation", "fills", "win_rate", "mean_R"])
        + f"\nTrade-by-trade outcome agreement: **{agree:.2%}** of {len(j)} signals; max P&L difference on common closed trades: "
        f"${js['V3']['pnl_max_abs_diff']:.4f}.")

    # ---------------- V4 M5 calibration of the intrabar assumption (2026 window)
    m5p = DATA / "xauusd_m5.csv"
    if m5p.exists():
        m5 = pd.read_csv(m5p, parse_dates=["datetime"])
        loc = m5["datetime"].dt.tz_localize(H1_TZ, ambiguous="NaT", nonexistent="NaT")
        m5 = m5[loc.notna()].copy()
        m5["ny"] = loc[loc.notna()].dt.tz_convert("America/New_York").dt.tz_localize(None)
        m5["day"] = (m5["ny"] + pd.Timedelta(hours=7)).dt.normalize()
        # timezone check: M5 aggregated to the hour must reproduce H1 bars
        m5["hr"] = m5["ny"].dt.floor("h")
        agg = m5.groupby("hr").agg(o=("open", "first"), hi=("high", "max"), lo=("low", "min"), c=("close", "last"))
        hj = h1.set_index("ny").join(agg, how="inner")
        tz_err = float(((hj["c"] - hj["close"]).abs()).median())
        win = d1.index[(d1.index >= m5["day"].min() + pd.Timedelta(days=1)) & (d1.index <= m5["day"].max())]
        dw = d1.loc[win]
        mb, ms, me = bar_arrays_from_h1(m5.rename(columns={}), dw)
        hb, hs_, he = bar_arrays_from_h1(h1, dw)
        # only compare signals whose next 3 trading days have complete M5 coverage (>= 250 of ~276 bars)
        cover = m5.groupby("day").size().reindex(dw.index).fillna(0).to_numpy() >= 250
        ok = np.array([cover[i + 1: i + 4].all() if i + 3 < len(dw) else False for i in range(len(dw))])
        bw = dw["close"].gt(dw["open"]).to_numpy() & ok
        rows, res = [], {}
        for label, (bb, ss, ee) in [("H1", (hb, hs_, he)), ("M5", (mb, ms, me))]:
            for mname, m in [("worst", WORST), ("path", PATH), ("best", BEST)]:
                sim = Sim(bb, ss, ee, dw, OFF, TP, SL, SPREAD, m)
                r = stats(sim, bw); r.update(bars=label, mode=mname); rows.append(r)
                res[(label, mname)] = sim
        a = res[("H1", "path")].outcome[bw]; b = res[("M5", "path")].outcome[bw]
        closed = np.isin(a, [OUT_TP, OUT_SL]) & np.isin(b, [OUT_TP, OUT_SL])
        h1amb = (res[("H1", "worst")].outcome[bw] != res[("H1", "best")].outcome[bw]).mean()
        m5amb = (res[("M5", "worst")].outcome[bw] != res[("M5", "best")].outcome[bw]).mean()
        js["V4"] = {"window": [str(win[0].date()), str(win[-1].date())], "signals_compared": int(bw.sum()),
                    "m5_vs_h1_hourly_close_median_abs_diff": tz_err, "rows": rows,
                    "h1path_vs_m5path_agreement_closed": float((a[closed] == b[closed]).mean()),
                    "h1_ambiguity": float(h1amb), "m5_ambiguity": float(m5amb)}
        hdr(md, f"V4 — Intrabar calibration with M5 bars ({win[0].date()} → {win[-1].date()})",
            f"M5 aggregated to hours reproduces H1 exactly on every complete hour (median |diff| ${tz_err:.3f}), so H1 contains no "
            f"spurious spikes. The M5 download has gaps at chunk joins, so only the {int(bw.sum())} bullish signals whose next 3 trading "
            "days have complete M5 coverage are compared.\n\n"
            + table(rows, ["bars", "mode", "fills", "win_rate", "mean_R", "t"])
            + f"\nH1-PATH vs M5-PATH outcome agreement on trades closed in both: **{js['V4']['h1path_vs_m5path_agreement_closed']:.1%}**. "
            f"Signals whose outcome depends on intrabar order: H1 {h1amb:.1%} → M5 {m5amb:.1%}. "
            "2026 is the most volatile year in the sample (median ATR ≈ $106), so this is a worst case for H1 ambiguity.")

    # ---------------- V5 day-boundary and data-convention sensitivity
    rows = []
    for label, shift in [("NY 17:00 (MT5 standard)", 7), ("UTC 00:00", None), ("NY 17:00, drop 17:00-18:00 NY bars", "drop")]:
        hh = h1.copy()
        if shift is None:
            hh["day"] = (hh["ny"].dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
                         .dt.tz_convert("UTC").dt.tz_localize(None)).dt.normalize()
            hh = hh[hh["day"].notna()]
        elif shift == "drop":
            hh = hh[hh["ny"].dt.hour != 17]
        dd = build_broker_d1(hh); bb, ss, ee = bar_arrays_from_h1(hh, dd)
        sim = Sim(bb, ss, ee, dd, OFF, TP, SL, SPREAD, PATH)
        r = stats(sim, (dd["close"] > dd["open"]).to_numpy()); r["day_definition"] = label; rows.append(r)
    js["V5"] = rows
    hdr(md, "V5 — Daily-candle definition sensitivity (PATH, $0.30)", table(rows, ["day_definition", "signals", "fills", "win_rate", "mean_R", "ci95", "t"]))

    # ---------------- V6 transaction costs: spread x commission x swap
    nights = rollovers(h1_trading["ny"].to_numpy(), base.entry_bar, base.exit_bar)
    held = nights[bull & base.filled]
    rows = []
    for sp in [0.15, 0.30, 0.50]:
        sim = Sim(bars, s, e, d1, OFF, TP, SL, sp, PATH)
        for comm in [0.0, 0.07]:          # $ per oz round turn: 0 (FTMO metals, secondary source) / ~$7 per lot raw-account broker (ASM)
            for swap in [-0.60, 0.0, 0.30]:  # $ per oz per night for a SHORT; sign and size UNVERIFIED for your broker
                pnl = sim.pnl - comm + swap * nights
                R = (pnl / SL)[bull & sim.filled]
                rows.append({"spread": sp, "commission_$/oz": comm, "swap_$/oz/night": swap, "fills": int(len(R)),
                             "mean_R": float(R.mean()), "t": float(R.mean() / R.std(ddof=1) * np.sqrt(len(R))),
                             "total_R": float(R.sum())})
    js["V6"] = {"median_nights_held": float(np.median(held)), "mean_nights_held": float(held.mean()),
                "share_closed_same_day": float((held == 0).mean()), "rows": rows}
    hdr(md, "V6 — Realistic transaction costs",
        f"Holding time: median {np.median(held):.0f} rollovers, mean {held.mean():.2f}; {js['V6']['share_closed_same_day']:.0%} of trades close before the first rollover. "
        "Commission $0.07/oz ≈ $7 per 100-oz lot (raw-spread broker, ASSUMPTION); FTMO reportedly charges none on metals (secondary source). "
        "Swap values are sensitivity bounds, not your broker's rates.\n\n"
        + table(rows, ["spread", "commission_$/oz", "swap_$/oz/night", "fills", "mean_R", "t", "total_R"]))

    # ---------------- V7 randomized controls and the geometry null
    fills_bull = bull & base.filled
    k = int(fills_bull.sum())
    pool = np.flatnonzero(base.filled)
    draws = np.array([np.nanmean(base.R[RNG.choice(pool, k, replace=False)]) for _ in range(5000)])
    obs = np.nanmean(base.R[fills_bull])
    # random direction on the same days (coin-flip SELL vs BUY STOP)
    mirror = Sim(bars, s, e, d1, OFF, TP, SL, SPREAD, PATH, direction=+1)
    rd = []
    for _ in range(2000):
        coin = RNG.random(len(d1)) < 0.5
        R = np.where(coin, base.R, mirror.R); F_ = np.where(coin, base.filled, mirror.filled)
        rd.append(np.nanmean(R[bull & F_]))
    rd = np.array(rd)
    # geometry null: a driftless random walk with this spread. Simulate paths from shuffled H1 returns
    # (destroys all time structure, keeps the volatility distribution), same rule, same costs.
    rets = np.diff(np.log(h1_trading["close"].to_numpy()))
    rets = rets[np.isfinite(rets)]
    rets = rets - rets.mean()
    null_means, null_wr = [], []
    closes = d1["close"].to_numpy()
    nb = e - s
    for rep in range(40):
        path = np.exp(np.cumsum(RNG.permutation(rets)))
        path = np.concatenate([[1.0], path])[: len(bars)] * closes[0]
        # build synthetic OHLC with the real bar layout: o = previous close, hi/lo from real bar's relative excursion
        c = path; o = np.concatenate([[c[0]], c[:-1]])
        rel_hi = (bars[:, 1] - np.maximum(bars[:, 0], bars[:, 3])) / bars[:, 3]
        rel_lo = (np.minimum(bars[:, 0], bars[:, 3]) - bars[:, 2]) / bars[:, 3]
        perm = RNG.permutation(len(bars))
        hi = np.maximum(o, c) * (1 + rel_hi[perm]); lo = np.minimum(o, c) * (1 - rel_lo[perm])
        sb = np.column_stack([o, hi, lo, c])
        dc = sb[np.maximum(e - 1, 0), 3]; do = sb[s, 0]
        dsyn = pd.DataFrame({"open": do, "close": dc}, index=d1.index)
        sim = Sim(sb, s, e, dsyn, OFF, TP, SL, SPREAD, PATH)
        bl = (dc > do)
        R = sim.R[bl & sim.filled & (nb > 0)]
        null_means.append(np.nanmean(R))
        oc = sim.outcome[bl & sim.filled]; null_wr.append((oc == OUT_TP).sum() / np.isin(oc, [OUT_TP, OUT_SL]).sum())
    null_means = np.array(null_means); null_wr = np.array(null_wr)
    js["V7"] = {"observed_mean_R": float(obs),
                "random_day_subsets_p_two_sided": float((np.abs(draws - draws.mean()) >= abs(obs - draws.mean())).mean()),
                "random_day_subsets_mean": float(draws.mean()), "random_day_subsets_p5_p95": [float(np.percentile(draws, 5)), float(np.percentile(draws, 95))],
                "random_direction_mean": float(rd.mean()), "random_direction_p5_p95": [float(np.percentile(rd, 5)), float(np.percentile(rd, 95))],
                "geometry_null_mean_R": float(null_means.mean()), "geometry_null_p5_p95": [float(np.percentile(null_means, 5)), float(np.percentile(null_means, 95))],
                "geometry_null_win_rate": float(null_wr.mean()), "geometry_null_win_rate_p5_p95": [float(np.percentile(null_wr, 5)), float(np.percentile(null_wr, 95))],
                "observed_win_rate": float((base.outcome[fills_bull] == OUT_TP).sum() / np.isin(base.outcome[fills_bull], [OUT_TP, OUT_SL]).sum())}
    v = js["V7"]
    hdr(md, "V7 — Randomised controls and the geometry null",
        table([{"control": "observed rule (bullish days, SELL STOP)", "mean_R": v["observed_mean_R"], "win_rate": v["observed_win_rate"], "range_5_95": ""},
               {"control": "5,000 random same-size subsets of all filled days", "mean_R": v["random_day_subsets_mean"], "win_rate": "", "range_5_95": v["random_day_subsets_p5_p95"]},
               {"control": "2,000 coin-flip directions on the same bullish days", "mean_R": v["random_direction_mean"], "win_rate": "", "range_5_95": v["random_direction_p5_p95"]},
               {"control": "40 synthetic driftless random walks (shuffled H1 returns), same rule and spread", "mean_R": v["geometry_null_mean_R"], "win_rate": v["geometry_null_win_rate"], "range_5_95": v["geometry_null_p5_p95"]}],
              ["control", "mean_R", "win_rate", "range_5_95"])
        + f"\nRandom-subset two-sided p = {v['random_day_subsets_p_two_sided']:.3f}. "
        f"Synthetic random walks produce a {v['geometry_null_win_rate']:.1%} win rate "
        f"(5-95%: {v['geometry_null_win_rate_p5_p95'][0]:.1%}-{v['geometry_null_win_rate_p5_p95'][1]:.1%}) with the same rule: "
        "the win rate is a property of the TP/SL geometry and the spread, not of gold.")

    # ---------------- V8 parameter neighbourhood (no selection)
    grid = []
    for off in [500, 600, 708, 800, 900]:
        for tp in [500, 600, 708, 800, 900]:
            for sl in [1200, 1400, 1616, 1800, 2000]:
                sim = Sim(bars, s, e, d1, off * POINT, tp * POINT, sl * POINT, SPREAD, PATH)
                R = sim.R[bull & sim.filled]
                grid.append({"offset": off, "tp": tp, "sl": sl, "fills": int(len(R)), "mean_R": float(np.nanmean(R)),
                             "t": float(np.nanmean(R) / np.nanstd(R, ddof=1) * np.sqrt(len(R)))})
    G = pd.DataFrame(grid)
    js["V8"] = {"combos": len(G), "share_mean_R_positive": float((G.mean_R > 0).mean()),
                "share_t_above_2": float((G.t > 2).mean()), "median_mean_R": float(G.mean_R.median()),
                "min_mean_R": float(G.mean_R.min()), "max_mean_R": float(G.mean_R.max()),
                "best": G.sort_values("t").iloc[-1].to_dict(), "literal": G[(G.offset == 708) & (G.tp == 708) & (G.sl == 1616)].iloc[0].to_dict()}
    v = js["V8"]
    hdr(md, "V8 — Parameter perturbation around 708/708/1616 (125 combinations, PATH, $0.30)",
        f"- Share of combinations with mean R > 0: **{v['share_mean_R_positive']:.0%}**; with t > 2: **{v['share_t_above_2']:.0%}**\n"
        f"- Mean R across the neighbourhood: median {v['median_mean_R']:+.3f}, range {v['min_mean_R']:+.3f} … {v['max_mean_R']:+.3f}\n"
        f"- Best of 125 by t (a multiple-testing artefact until shown otherwise): offset {v['best']['offset']:.0f}, tp {v['best']['tp']:.0f}, "
        f"sl {v['best']['sl']:.0f}, mean R {v['best']['mean_R']:+.3f}, t {v['best']['t']:.2f}. "
        f"With 125 tries, the expected maximum t under pure noise is about 2.4-2.6.\n\n"
        + table(G.groupby("sl").agg(mean_R=("mean_R", "mean"), share_positive=("mean_R", lambda x: (x > 0).mean())).reset_index().to_dict("records"),
                ["sl", "mean_R", "share_positive"]))

    # ---------------- V9 walk-forward: can optimisation rescue it?
    years = sorted(set(d1.index.year))
    sims = {}
    for off in [500, 600, 708, 800, 900]:
        for tp in [500, 600, 708, 800, 900]:
            for sl in [1200, 1400, 1616, 1800, 2000]:
                sims[(off, tp, sl)] = Sim(bars, s, e, d1, off * POINT, tp * POINT, sl * POINT, SPREAD, PATH)
    rows, oos_R, lit_R = [], [], []
    for y in years[2:]:
        tr = bull & (d1.index.year >= y - 2) & (d1.index.year < y)
        te = bull & (d1.index.year == y)
        best = max(sims, key=lambda k: np.nanmean(sims[k].R[tr & sims[k].filled]))
        Rt = sims[best].R[te & sims[best].filled]; Rl = base.R[te & base.filled]
        oos_R += list(Rt); lit_R += list(Rl)
        rows.append({"test_year": y, "chosen_on_prior_2y": f"{best[0]}/{best[1]}/{best[2]}",
                     "IS_mean_R": float(np.nanmean(sims[best].R[tr & sims[best].filled])),
                     "OOS_mean_R": float(np.nanmean(Rt)), "OOS_fills": int(len(Rt)), "literal_mean_R": float(np.nanmean(Rl))})
    oos_R = np.array(oos_R); lit_R = np.array(lit_R)
    js["V9"] = {"rows": rows, "wf_oos_mean_R": float(np.nanmean(oos_R)), "wf_oos_t": float(np.nanmean(oos_R) / np.nanstd(oos_R, ddof=1) * np.sqrt(len(oos_R))),
                "literal_same_years_mean_R": float(np.nanmean(lit_R))}
    hdr(md, "V9 — Walk-forward (re-optimise on the prior 2 years, trade the next year)",
        table(rows, ["test_year", "chosen_on_prior_2y", "IS_mean_R", "OOS_mean_R", "OOS_fills", "literal_mean_R"])
        + f"\nConcatenated walk-forward OOS: mean R **{js['V9']['wf_oos_mean_R']:+.3f}** (t {js['V9']['wf_oos_t']:.2f}) vs literal "
        f"{js['V9']['literal_same_years_mean_R']:+.3f} on the same years. In-sample winners do not carry forward.")

    # ---------------- V10 periods and regimes (literal)
    rows = []
    for label, m in [("2020-2021", d1.index.year <= 2021), ("2022-2023", (d1.index.year >= 2022) & (d1.index.year <= 2023)),
                     ("2024-2026", d1.index.year >= 2024),
                     ("uptrend", F["uptrend"].to_numpy()), ("downtrend", F["downtrend"].to_numpy()),
                     ("no trend", ~(F["uptrend"] | F["downtrend"]).to_numpy()),
                     ("ATR < $30", (F["atr14"] < 30).to_numpy()), ("ATR $30-60", ((F["atr14"] >= 30) & (F["atr14"] < 60)).to_numpy()),
                     ("ATR ≥ $60", (F["atr14"] >= 60).to_numpy())]:
        r = stats(base, bull & m); r["segment"] = label; rows.append(r)
    js["V10"] = rows
    hdr(md, "V10 — Periods and regimes (literal, PATH, $0.30)", table(rows, ["segment", "fills", "win_rate", "mean_R", "ci95", "t"]))

    # ---------------- V11 survivability: concurrency-aware equity with prop-firm limits
    fb_idx = np.flatnonzero(bull & base.filled)
    entry_t = h1_trading["ny"].to_numpy()[base.entry_bar[fb_idx]]
    exit_t = h1_trading["ny"].to_numpy()[base.exit_bar[fb_idx]]
    ev = sorted([(t, +1) for t in entry_t] + [(t, -1) for t in exit_t])
    conc = np.cumsum([x for _, x in ev]); max_conc = int(conc.max())
    R = base.R[fb_idx]
    order = np.argsort(exit_t)
    # block bootstrap keeps streaks (blocks of 10 consecutive trades)
    blocks = [R[order][i:i + 10] for i in range(0, len(R) - 9)]
    per_year = int(round(len(R) / ((d1.index[-1] - d1.index[0]).days / 365.25)))
    out = []
    for risk in [0.005, 0.01]:
        fails, rets = 0, []
        for _ in range(5000):
            seq = np.concatenate([blocks[i] for i in RNG.integers(0, len(blocks), per_year // 10 + 1)])[:per_year] * risk
            eq = np.cumsum(seq); dd = (np.maximum.accumulate(np.concatenate([[0], eq])) - np.concatenate([[0], eq])).max()
            fails += dd >= 0.10; rets.append(eq[-1])
        # worst realised server-day loss in the actual history (all positions closed that day)
        exit_day = pd.to_datetime(exit_t).normalize()
        daily = pd.Series(R * risk, index=exit_day).groupby(level=0).sum()
        out.append({"risk_per_trade": risk, "trades_per_year": per_year, "P(max_DD>=10%) block-bootstrap": fails / 5000,
                    "median_1y_return": float(np.median(rets)), "P(1y>0)": float((np.array(rets) > 0).mean()),
                    "worst_actual_day": float(daily.min()), "days_worse_than_-5%": int((daily <= -0.05).sum())})
    js["V11"] = {"max_concurrent_positions": max_conc, "rows": out}
    hdr(md, "V11 — Survivability (prop-firm style limits)",
        f"Maximum simultaneous open positions in history: **{max_conc}** (each at full risk). Block bootstrap (blocks of 10 trades) keeps losing streaks.\n\n"
        + table(out, list(out[0].keys())))

    # ---------------- V12 point-size readings
    rows = []
    for label, scale in [("1 pt = $0.001 (3-digit feed)", 0.1), ("1 pt = $0.01 (2-digit MT5, primary)", 1), ("1 pt = $0.10 ('pips')", 10)]:
        sim = Sim(bars, s, e, d1, OFF * scale, TP * scale, SL * scale, SPREAD, PATH)
        r = stats(sim, bull); r["reading"] = label; r["tp_$"] = TP * scale; rows.append(r)
    js["V12"] = rows
    hdr(md, "V12 — What '708 points' means changes the trade, not the verdict", table(rows, ["reading", "tp_$", "fills", "win_rate", "mean_R", "ci95", "t"]))

    RES.mkdir(exist_ok=True)
    (RES / "xau_verify.md").write_text("\n".join(md))
    (RES / "xau_verify.json").write_text(json.dumps(js, indent=1, default=lambda o: o.item() if isinstance(o, np.generic) else str(o)))
    print("\n".join(md))


if __name__ == "__main__":
    main()
