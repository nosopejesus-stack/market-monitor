"""XAUUSD 'SELL STOP after bullish daily close' falsification study.

Run from quant/:  python -m xau.study
Writes results/xau_study.md (tables) and results/xau_study.json (raw numbers).

Every number in the report is produced here; nothing is typed by hand.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import load_h1, build_broker_d1, bar_arrays_from_h1, load_native_d1, bar_arrays_from_d1
from .engine import simulate, WORST, PATH, BEST, OUT_TP, OUT_SL, OUT_OPEN, OUT_NOFILL
from .features import daily_features

RES = Path(__file__).resolve().parents[1] / "results"
RES.mkdir(exist_ok=True)
RNG = np.random.default_rng(20260924)
MODES = {"worst": WORST, "path": PATH, "best": BEST}
BASE_SPREAD = 0.30   # ASSUMPTION: typical retail XAUUSD spread in USD; sensitivity is reported
POINT = 0.01         # ASSUMPTION: MT5 2-digit XAUUSD, 1 point = $0.01
OFF, TP, SL = 708 * POINT, 708 * POINT, 1616 * POINT
IS_END = pd.Timestamp("2022-12-31")


class Sim:
    """All-days simulation for one config, reusable across condition masks."""

    def __init__(self, bars, start, end, d1, off, tp, sl, spread, mode, direction=-1, expiry=1):
        n = len(d1)
        arr = lambda v: np.broadcast_to(np.asarray(v, float), (n,)).copy()  # noqa: E731
        self.sl = arr(sl)
        o, p, eb, xb = simulate(bars, start, end, d1["close"].to_numpy(float), direction,
                                arr(off), arr(tp), self.sl, spread, expiry, 0, mode)
        self.outcome, self.pnl, self.entry_bar, self.exit_bar = o, p, eb, xb
        self.R = np.where(self.sl > 0, p / self.sl, np.nan)
        self.filled = o != OUT_NOFILL
        self.idx = d1.index


def stats(sim: Sim, mask, n_perm=0, perm_pool=None):
    mask = np.asarray(mask, bool) & ~np.isnan(sim.R)
    f = mask & sim.filled
    R = sim.R[f]
    closed = f & (sim.outcome != OUT_OPEN)
    tp_n = int((sim.outcome[f] == OUT_TP).sum()); sl_n = int((sim.outcome[f] == OUT_SL).sum())
    years = max((sim.idx[-1] - sim.idx[0]).days / 365.25, 1e-9)
    out = {"signals": int(mask.sum()), "fills": int(f.sum()), "tp": tp_n, "sl": sl_n,
           "open": int((sim.outcome[f] == OUT_OPEN).sum()),
           "fill_rate": f.sum() / max(mask.sum(), 1),
           "win_rate": tp_n / max(closed.sum(), 1),
           "mean_R": float(R.mean()) if len(R) else np.nan,
           "t": float(R.mean() / R.std(ddof=1) * np.sqrt(len(R))) if len(R) > 2 and R.std() > 0 else np.nan,
           "pf": float(R[R > 0].sum() / -R[R < 0].sum()) if (R < 0).any() else np.nan,
           "total_R": float(R.sum()), "trades_per_year": f.sum() / years}
    if len(R) > 2:
        eq = np.cumsum(R[np.argsort(sim.exit_bar[f], kind="stable")])
        out["max_dd_R"] = float((np.maximum.accumulate(np.concatenate([[0], eq])) - np.concatenate([[0], eq])).max())
        bs = RNG.choice(R, size=(2000, len(R)), replace=True).mean(1)
        out["ci95"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    if n_perm and perm_pool is not None:
        pool = np.flatnonzero(perm_pool & sim.filled & ~np.isnan(sim.R))
        k = len(R)
        if 0 < k < len(pool):
            draws = np.array([sim.R[RNG.choice(pool, k, replace=False)].mean() for _ in range(n_perm)])
            # two-sided: how often does a random subset look at least this different from the pool mean
            mu = sim.R[pool].mean()
            out["perm_p"] = float((np.abs(draws - mu) >= abs(R.mean() - mu)).mean())
    return out


def fmt(x, p=3):
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(fmt(v, p) for v in x) + "]"
    if isinstance(x, (float, np.floating)):
        return "—" if np.isnan(x) else f"{x:.{p}f}"
    return str(x)


def table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "\n".join("| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |" for r in rows) + "\n"


def bh(pvals):
    p = np.asarray(pvals, float); n = len(p); order = np.argsort(p)
    q = np.empty(n); prev = 1.0
    for rank, i in enumerate(order[::-1]):
        k = n - rank
        prev = min(prev, p[i] * n / k); q[i] = prev
    return q


def main():
    md, js = [], {}
    h1 = load_h1(); d1 = build_broker_d1(h1); bars, s, e = bar_arrays_from_h1(h1, d1)
    F = daily_features(d1)
    bull = F["bull"].to_numpy(); bear = F["bear"].to_numpy(); alld = np.ones(len(d1), bool)
    is_mask = (d1.index <= IS_END); oos_mask = ~is_mask
    md.append(f"# XAUUSD SELL-STOP study — generated tables\n\nData: Twelve Data XAU/USD H1 → MT5-style daily bars "
              f"(NY 17:00), {d1.index[0].date()} → {d1.index[-1].date()}, {len(d1)} trading days, {len(bars)} H1 bars.\n"
              f"Literal rule: after a bullish daily close C, SELL STOP at C−{OFF:.2f}, TP {TP:.2f}, SL {SL:.2f} (1 point = ${POINT}). "
              f"Order valid for the next trading day only; held until TP/SL. R = SL distance. Base spread ${BASE_SPREAD} (assumption).\n")

    # --- T1: literal rule, ambiguity bounds, spread sensitivity
    rows = []
    for sp in [0.0, 0.2, 0.3, 0.5, 1.0]:
        for mname, m in MODES.items():
            sim = Sim(bars, s, e, d1, OFF, TP, SL, sp, m)
            r = stats(sim, bull); r.update(spread=sp, mode=mname); rows.append(r)
    js["T1_literal"] = rows
    md.append("## T1 — Literal rule (bullish close → SELL STOP 708/708/1616 pts)\n\n"
              "Random-walk breakeven win rate for TP 708 / SL 1616 is 1616/(708+1616) = **69.5%**.\n\n"
              + table(rows, ["spread", "mode", "signals", "fills", "win_rate", "mean_R", "ci95", "t", "pf", "max_dd_R", "trades_per_year"]))

    base = Sim(bars, s, e, d1, OFF, TP, SL, BASE_SPREAD, PATH)
    worst = Sim(bars, s, e, d1, OFF, TP, SL, BASE_SPREAD, WORST)
    best = Sim(bars, s, e, d1, OFF, TP, SL, BASE_SPREAD, BEST)
    amb = (base.filled & bull & (worst.outcome != best.outcome)).sum() / max((base.filled & bull).sum(), 1)
    js["ambiguity_rate"] = float(amb)
    md.append(f"\nShare of filled trades whose outcome depends on intrabar order (WORST≠BEST): **{amb:.1%}**. "
              "PATH is the standard OHLC path assumption; WORST/BEST are hard bounds.\n")

    # --- T2: controls
    mirror = Sim(bars, s, e, d1, OFF, TP, SL, BASE_SPREAD, PATH, direction=+1)
    rows = []
    for name, sim, mask in [("bullish → SELL STOP (hypothesis)", base, bull),
                            ("every day → SELL STOP", base, alld),
                            ("bearish → SELL STOP", base, bear),
                            ("bullish → BUY STOP (mirror)", mirror, bull),
                            ("every day → BUY STOP", mirror, alld)]:
        r = stats(sim, mask, n_perm=2000 if mask is bull and sim is base else 0, perm_pool=alld)
        r["test"] = name; rows.append(r)
    js["T2_controls"] = rows
    md.append("\n## T2 — Controls (PATH, base spread)\n\n`perm_p`: share of 2000 random same-size day subsets "
              "whose mean R differs from the all-days mean by at least as much as the bullish-day subset does.\n\n"
              + table(rows, ["test", "signals", "fills", "win_rate", "mean_R", "ci95", "t", "perm_p"]))

    # --- T3: by year and IS/OOS
    rows = []
    for y in sorted(set(d1.index.year)):
        r = stats(base, bull & (d1.index.year == y)); r["period"] = str(y)
        r["median_atr"] = float(F["atr14"][d1.index.year == y].median()); rows.append(r)
    for nm, m in [("IS 2020-2022", is_mask), ("OOS 2023-2026", oos_mask)]:
        r = stats(base, bull & m); r["period"] = nm; rows.append(r)
    js["T3_by_year"] = rows
    md.append("\n## T3 — Stability by year (PATH, base spread)\n\n"
              + table(rows, ["period", "median_atr", "fills", "fill_rate", "win_rate", "mean_R", "ci95", "t", "max_dd_R"]))

    # --- T4: conditional slices, thresholds from IS only (no look-ahead in cut points)
    Fi = F[is_mask]
    def terc(col):
        q1, q2 = Fi.loc[Fi["bull"], col].quantile([1 / 3, 2 / 3])
        v = F[col].to_numpy()
        return {f"{col} low (<{q1:.2f})": v < q1, f"{col} mid": (v >= q1) & (v < q2), f"{col} high (≥{q2:.2f})": v >= q2}
    slices = {"1 bullish candle only (run==1)": F["bull_run"].to_numpy() == 1,
              "2 consecutive bullish (run==2)": F["bull_run"].to_numpy() == 2,
              "3+ consecutive bullish (run≥3)": F["bull_run"].to_numpy() >= 3,
              "two large bullish recovery candles": F["two_large_recovery"].to_numpy(),
              "uptrend (C>SMA200, SMA50>SMA200)": F["uptrend"].to_numpy(),
              "downtrend": F["downtrend"].to_numpy(),
              "no clear trend": ~(F["uptrend"] | F["downtrend"]).to_numpy(),
              "next day = NFP proxy (1st Fri)": F["next_day_nfp_proxy"].to_numpy(),
              "next day ≠ NFP proxy": ~F["next_day_nfp_proxy"].to_numpy()}
    for col in ["body_atr", "upper_wick_frac", "lower_wick_frac", "close_pos", "vol_regime",
                "trend_strength", "dist_high20_atr", "dist_low20_atr", "atr14"]:
        slices.update(terc(col))
    for wd, nm in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
        slices[f"signal day {nm}"] = F["weekday"].to_numpy() == wd
    # fill session (NY clock of the entry bar) — descriptive, only known after the fill
    ny_hour = np.full(len(d1), -1)
    fb = base.entry_bar >= 0
    ny_hour[fb] = h1[h1["day"].isin(d1.index)].reset_index(drop=True)["ny"].dt.hour.to_numpy()[base.entry_bar[fb]]
    slices["fill in Asia (18-02 NY)"] = fb & ((ny_hour >= 18) | (ny_hour < 2))
    slices["fill in London (02-08 NY)"] = fb & (ny_hour >= 2) & (ny_hour < 8)
    slices["fill in New York (08-17 NY)"] = fb & (ny_hour >= 8) & (ny_hour < 17)
    rows = []
    for nm, m in slices.items():
        m = np.asarray(m, bool)
        r_all = stats(base, bull & m, n_perm=1000, perm_pool=bull)
        r_is = stats(base, bull & m & is_mask); r_oos = stats(base, bull & m & oos_mask)
        rows.append({"slice": nm, "fills": r_all["fills"], "win_rate": r_all["win_rate"], "mean_R": r_all["mean_R"],
                     "t": r_all["t"], "perm_p": r_all.get("perm_p", np.nan),
                     "IS_fills": r_is["fills"], "IS_mean_R": r_is["mean_R"], "IS_t": r_is["t"],
                     "OOS_fills": r_oos["fills"], "OOS_mean_R": r_oos["mean_R"], "OOS_t": r_oos["t"]})
    q = bh([r["perm_p"] if not np.isnan(r["perm_p"]) else 1.0 for r in rows])
    for r, qq in zip(rows, q):
        r["BH_q"] = float(qq)
    js["T4_slices"] = rows
    md.append(f"\n## T4 — Conditional slices of bullish days ({len(rows)} slices tested)\n\n"
              "Tercile cut points are estimated on IS (2020-2022) bullish days only. `perm_p` compares each slice with random "
              "same-size subsets of all bullish-day fills; `BH_q` is the Benjamini-Hochberg false-discovery-adjusted value "
              "across all slices.\n\n"
              + table(rows, ["slice", "fills", "win_rate", "mean_R", "t", "perm_p", "BH_q",
                             "IS_fills", "IS_mean_R", "IS_t", "OOS_fills", "OOS_mean_R", "OOS_t"]))

    # --- T5: select on IS, test on OOS (the honest way to 'discover' a filter)
    cand = [r for r in rows if r["IS_fills"] >= 30 and not np.isnan(r["IS_t"]) and "fill in" not in r["slice"]]
    top = sorted(cand, key=lambda r: -r["IS_t"])[:5]
    js["T5_selected"] = top
    md.append("\n## T5 — Pick the 5 best slices on IS, then look at OOS\n\n"
              + table(top, ["slice", "IS_fills", "IS_mean_R", "IS_t", "OOS_fills", "OOS_mean_R", "OOS_t"]))

    # --- T6: parameter robustness — ATR-scaled geometry, and the x10 point reading
    atr = F["atr14"].to_numpy()
    ratio = SL / TP
    rows = []
    for k in [0.1, 0.2, 0.3, 0.5, 0.75, 1.0]:
        for rr in [1.5, ratio, 3.0]:
            sim = Sim(bars, s, e, d1, k * atr, k * atr, k * rr * atr, BASE_SPREAD, PATH)
            rb = stats(sim, bull); ra = stats(sim, alld)
            rows.append({"offset=tp (xATR)": k, "sl/tp": rr, "bull_fills": rb["fills"], "bull_win_rate": rb["win_rate"],
                         "bull_mean_R": rb["mean_R"], "bull_t": rb["t"], "all_mean_R": ra["mean_R"],
                         "bull_minus_all": rb["mean_R"] - ra["mean_R"]})
    x10 = Sim(bars, s, e, d1, OFF * 10, TP * 10, SL * 10, BASE_SPREAD, PATH)
    r = stats(x10, bull); rx = stats(x10, alld)
    rows.append({"offset=tp (xATR)": "x10 pts ($70.8)", "sl/tp": ratio, "bull_fills": r["fills"], "bull_win_rate": r["win_rate"],
                 "bull_mean_R": r["mean_R"], "bull_t": r["t"], "all_mean_R": rx["mean_R"], "bull_minus_all": r["mean_R"] - rx["mean_R"]})
    js["T6_robustness_h1"] = rows
    md.append("\n## T6 — Parameter robustness (H1 era, PATH, base spread)\n\nOffset = TP = k·ATR14, SL = (sl/tp)·TP. "
              "`bull_minus_all` isolates what the bullish-close condition adds over placing the same order every day.\n\n"
              + table(rows, list(rows[0].keys())))

    # --- T7: independent era 2006-2019 on native daily bars (bounds only: daily bars cannot order intraday events)
    dn = load_native_d1(); Fn = daily_features(dn); bn, sn, en = bar_arrays_from_d1(dn)
    rows = []
    for k in [0.2, 0.3, 0.5, 1.0]:
        for mname in ["worst", "best"]:
            a = Fn["atr14"].to_numpy()
            sim = Sim(bn, sn, en, dn, k * a, k * a, k * ratio * a, BASE_SPREAD, MODES[mname])
            rb = stats(sim, Fn["bull"].to_numpy()); ra = stats(sim, np.ones(len(dn), bool))
            rows.append({"k (xATR)": k, "mode": mname, "bull_fills": rb["fills"], "bull_win_rate": rb["win_rate"],
                         "bull_mean_R": rb["mean_R"], "all_mean_R": ra["mean_R"], "bull_minus_all": rb["mean_R"] - ra["mean_R"]})
    for mname in ["worst", "best"]:
        sim = Sim(bn, sn, en, dn, OFF, TP, SL, BASE_SPREAD, MODES[mname])
        rb = stats(sim, Fn["bull"].to_numpy()); ra = stats(sim, np.ones(len(dn), bool))
        rows.append({"k (xATR)": "literal $7.08/$16.16", "mode": mname, "bull_fills": rb["fills"], "bull_win_rate": rb["win_rate"],
                     "bull_mean_R": rb["mean_R"], "all_mean_R": ra["mean_R"], "bull_minus_all": rb["mean_R"] - ra["mean_R"]})
    js["T7_d1_2006_2019"] = rows
    md.append(f"\n## T7 — Independent era: native daily bars {dn.index[0].date()} → {dn.index[-1].date()} ({len(dn)} days)\n\n"
              "Daily bars cannot tell whether TP or SL came first, so only WORST/BEST bounds are meaningful. "
              "The day boundary of these native bars is not verified to be NY 17:00.\n\n" + table(rows, list(rows[0].keys())))

    # --- T8: Monte Carlo of a prop-firm style account on the literal rule
    R = base.R[bull & base.filled]
    per_year = int(round(stats(base, bull)["trades_per_year"]))
    rows = []
    for risk in [0.005, 0.01]:
        paths = RNG.choice(R, size=(10000, per_year), replace=True) * risk
        eq = np.cumsum(paths, 1)
        dd = (np.maximum.accumulate(np.concatenate([np.zeros((10000, 1)), eq], 1), 1)
              - np.concatenate([np.zeros((10000, 1)), eq], 1)).max(1)
        rows.append({"risk_per_trade": risk, "trades": per_year, "median_1y_return": float(np.median(eq[:, -1])),
                     "p5_1y_return": float(np.percentile(eq[:, -1], 5)), "p95_1y_return": float(np.percentile(eq[:, -1], 95)),
                     "P(1y return>0)": float((eq[:, -1] > 0).mean()), "P(maxDD>=5%)": float((dd >= 0.05).mean()),
                     "P(maxDD>=10%)": float((dd >= 0.10).mean())})
    js["T8_montecarlo"] = rows
    md.append("\n## T8 — Monte Carlo (bootstrap of literal-rule trades, PATH, base spread, 10,000 one-year paths)\n\n"
              "Simple (non-compounded) returns; assumes trades are independent draws from the 2020-2026 distribution.\n\n"
              + table(rows, list(rows[0].keys())))

    # --- T9: post-hoc filters surfaced by T4, re-tested where they were NOT discovered (2006-2019 daily bars)
    body_cut = float(Fi.loc[Fi["bull"], "body_atr"].quantile(2 / 3))
    rows = []
    for era, dd, FF, (bb, ss, ee) in [("2020-2026 H1 (discovery era)", d1, F, (bars, s, e)),
                                       ("2006-2019 D1 (independent era)", dn, Fn, (bn, sn, en))]:
        modes = ["path"] if era.startswith("2020") else ["worst", "best"]
        bl = FF["bull"].to_numpy()
        filt = {"all bullish (baseline)": bl,
                f"bullish & body < {body_cut:.2f} ATR": bl & (FF["body_atr"].to_numpy() < body_cut),
                f"bullish & body >= {body_cut:.2f} ATR": bl & (FF["body_atr"].to_numpy() >= body_cut),
                "3+ consecutive bullish": FF["bull_run"].to_numpy() >= 3}
        for mname in modes:
            sim = Sim(bb, ss, ee, dd, OFF, TP, SL, BASE_SPREAD, MODES[mname])
            for fn, m in filt.items():
                r = stats(sim, m, n_perm=1000, perm_pool=bl); r.update(era=era, mode=mname, filter=fn); rows.append(r)
    js["T9_posthoc_filters"] = rows
    md.append("\n## T9 — Post-hoc filters re-tested out of era (literal geometry, base spread)\n\n"
              "These filters were noticed in T4 (2020-2026), so 2020-2026 numbers are NOT evidence. "
              "The 2006-2019 daily bars are untouched by the selection but only give WORST/BEST bounds. "
              "`perm_p` compares the filter with random same-size subsets of that era's bullish days under the same mode.\n\n"
              + table(rows, ["era", "mode", "filter", "fills", "win_rate", "mean_R", "ci95", "t", "perm_p"]))

    (RES / "xau_study.md").write_text("\n".join(md))
    (RES / "xau_study.json").write_text(json.dumps(js, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item()))
    print("\n".join(md))


if __name__ == "__main__":
    main()
