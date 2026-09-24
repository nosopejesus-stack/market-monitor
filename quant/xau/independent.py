"""Independent re-implementation of the literal rule, for cross-checking engine.py.

Written from the rule text, sharing no simulation code with engine.py: plain Python,
pandas groupby for day membership, explicit price-path walk per bar. If both
implementations agree trade by trade, a coding error in either is unlikely.
"""
from __future__ import annotations

import pandas as pd


def bar_path(o, h, l, c):
    # Standard OHLC path assumption: a down bar visits the high first, an up bar the low first.
    return [o, h, l, c] if c < o else [o, l, h, c]


def simulate_short(h1: pd.DataFrame, days: pd.DatetimeIndex, closes: pd.Series, signal_days,
                   offset: float, tp: float, sl: float, spread: float) -> pd.DataFrame:
    """SELL STOP at close - offset, valid for the next trading day only; exits TP/SL only.

    h1 must contain columns ny, day, open, high, low, close for trading days only.
    Returns one row per signal day: filled, outcome ('TP'|'SL'|'OPEN'|'NOFILL'), pnl.
    """
    half = spread / 2
    by_day = {d: g[["open", "high", "low", "close"]].to_numpy() for d, g in h1.groupby("day")}
    order = list(days)
    pos = {d: i for i, d in enumerate(order)}
    rows = []
    for sd in signal_days:
        i = pos[sd]
        if i + 1 >= len(order):
            continue
        entry = closes[sd] - offset
        take, stop = entry - tp, entry + sl
        state, fill, result = "pending", None, None
        for j in range(i + 1, len(order)):
            if state == "pending" and j > i + 1:
                break  # order expired at the end of the next day
            for o, hi, lo, c in by_day.get(order[j], []):
                if state == "pending":
                    if o - half <= entry:           # gapped through the stop at the open
                        state, fill = "open", o - half
                        pts = [o, hi, lo, c][1:] if c < o else [o, lo, hi, c][1:]
                        prev = o
                    elif lo - half <= entry:
                        state, fill = "open", entry
                        path = bar_path(o, hi, lo, c)
                        # walk until the entry is crossed, then continue from the entry level
                        k = 0
                        while k < 3 and not min(path[k], path[k + 1]) - half <= entry:
                            k += 1
                        prev, pts = entry, path[k + 1:]
                    else:
                        continue
                    for p in pts:  # remainder of the fill bar
                        if p > prev and p + half >= stop:
                            result = ("SL", fill - stop); break
                        if p < prev and p + half <= take:
                            result = ("TP", fill - take); break
                        prev = p
                    if result:
                        break
                    continue
                # position open: new bar
                if o + half >= stop:
                    result = ("SL", fill - (o + half)); break
                if o + half <= take:
                    result = ("TP", fill - (o + half)); break
                prev = o
                for p in bar_path(o, hi, lo, c)[1:]:
                    if p > prev and p + half >= stop:
                        result = ("SL", fill - stop); break
                    if p < prev and p + half <= take:
                        result = ("TP", fill - take); break
                    prev = p
                if result:
                    break
            if result:
                break
        if state == "pending":
            rows.append((sd, False, "NOFILL", 0.0))
        elif result is None:
            rows.append((sd, True, "OPEN", float("nan")))
        else:
            rows.append((sd, True, result[0], result[1]))
    return pd.DataFrame(rows, columns=["day", "filled", "outcome", "pnl"]).set_index("day")
