"""Event simulator for a pending STOP entry placed at the close of day t.

For every day t the simulator answers: if an order had been placed at the close of
day t, what would have happened? Conditions (e.g. "bullish candle") are applied
later as masks over this all-days result, which makes random-subset controls cheap
and guarantees conditioned and unconditioned results use identical mechanics.

Order model (direction = -1 SELL STOP, +1 BUY STOP):
  entry  E  = close_t + direction * offset
  TP        = E + direction * tp
  SL        = E - direction * sl
  valid for `expiry_days` trading days after day t, then cancelled.
  Once filled, held until TP or SL (optionally a max holding period).

Price data is treated as MID. A spread `s` is applied as half-spread on each side:
  a sell order triggers when mid <= level + s/2 (bid touches), a buy when mid >= level - s/2.
Gaps: a stop order that is gapped through fills at the bar open (+/- s/2 slippage).

Intrabar ambiguity (a bar that could have hit TP and SL) is resolved three ways:
  WORST = adverse outcome first (lower bound), BEST = favourable first (upper bound),
  PATH  = standard OHLC path assumption (bearish bar O-H-L-C, bullish bar O-L-H-C).
Using H1 bars inside daily signals keeps the WORST/BEST gap small; the report shows it.
"""
import numpy as np
from numba import njit

WORST, PATH, BEST = 0, 1, 2
OUT_NOFILL, OUT_TP, OUT_SL, OUT_OPEN = 0, 1, -1, 2


@njit(cache=True)
def _path_points(o, h, l, c):
    if c < o:
        return (o, h, l, c)
    return (o, l, h, c)


@njit(cache=True)
def simulate(bars, day_start, day_end, closes, direction, offset, tp, sl,
             spread, expiry_days, max_hold_days, mode):
    """Returns (outcome, pnl, entry_bar, exit_bar) arrays, one row per day t.

    offset/tp/sl are per-day arrays (allowing ATR-scaled variants).
    pnl is in price units per 1 unit (oz), net of spread.
    """
    nd = closes.shape[0]
    outcome = np.zeros(nd, np.int8)
    pnl = np.zeros(nd)
    entry_bar = -np.ones(nd, np.int64)
    exit_bar = -np.ones(nd, np.int64)
    hs = spread / 2.0
    d = direction
    for t in range(nd - 1):
        E = closes[t] + d * offset[t]
        TP = E + d * tp[t]
        SL = E - d * sl[t]
        first = day_start[t + 1]
        last_entry_day = min(t + expiry_days, nd - 1)
        entry_end = day_end[last_entry_day]
        if max_hold_days > 0:
            hold_end = day_end[min(t + expiry_days + max_hold_days, nd - 1)]
        else:
            hold_end = bars.shape[0]
        filled = False
        fill_px = 0.0
        done = False
        for b in range(first, hold_end):
            o = bars[b, 0]; hi = bars[b, 1]; lo = bars[b, 2]; cl = bars[b, 3]
            fill_bar = False
            if not filled:
                if b >= entry_end:
                    break
                # entry trigger for this bar
                if d < 0:
                    trig = lo - hs <= E
                    gap = o - hs <= E
                else:
                    trig = hi + hs >= E
                    gap = o + hs >= E
                if not trig:
                    continue
                filled = True
                fill_bar = True
                entry_bar[t] = b
                fill_px = (o - hs) if (gap and d < 0) else ((o + hs) if (gap and d > 0) else E)
            # exit checks (short: TP below, SL above; long mirrored)
            if d < 0:
                tp_hit = lo + hs <= TP
                sl_hit = hi + hs >= SL
                sl_gap = o + hs >= SL and not fill_bar
                tp_gap = o + hs <= TP and not fill_bar
            else:
                tp_hit = hi - hs >= TP
                sl_hit = lo - hs <= SL
                sl_gap = o - hs <= SL and not fill_bar
                tp_gap = o - hs >= TP and not fill_bar
            if not (tp_hit or sl_hit):
                continue
            res = 0
            if sl_gap:
                res = -1
            elif tp_gap:
                res = 1
            elif tp_hit and not sl_hit:
                res = 1
            elif sl_hit and not tp_hit:
                if fill_bar and mode == BEST:
                    # SL certain only if the close is beyond SL (price moved there after the fill)
                    beyond = (cl + hs >= SL) if d < 0 else (cl - hs <= SL)
                    res = -1 if beyond else 0
                elif fill_bar and mode == PATH:
                    res = _resolve_path(o, hi, lo, cl, d, E, TP, SL, hs, True)
                else:
                    res = -1
            else:  # both reachable in this bar
                if mode == WORST:
                    res = -1
                elif mode == BEST:
                    res = 1
                else:
                    res = _resolve_path(o, hi, lo, cl, d, E, TP, SL, hs, fill_bar)
            if res == 0:
                continue
            exit_bar[t] = b
            if res == 1:
                outcome[t] = OUT_TP
                px = TP
                if tp_gap:
                    px = o + hs if d < 0 else o - hs
                pnl[t] = d * (px - fill_px)
            else:
                outcome[t] = OUT_SL
                px = SL
                if sl_gap:
                    px = o + hs if d < 0 else o - hs
                pnl[t] = d * (px - fill_px)
            done = True
            break
        if filled and not done:
            outcome[t] = OUT_OPEN
            b = min(hold_end, bars.shape[0]) - 1
            exit_bar[t] = b
            # mark to market: a short buys back at ask, a long sells at bid
            pnl[t] = d * (bars[b, 3] - d * hs - fill_px)
    return outcome, pnl, entry_bar, exit_bar


@njit(cache=True)
def _resolve_path(o, h, l, c, d, E, TP, SL, hs, from_fill_search):
    """Walk the assumed OHLC path; return 1 (TP), -1 (SL) or 0 (neither after fill)."""
    pts = _path_points(o, h, l, c)
    filled = not from_fill_search
    for i in range(3):
        a = pts[i]; b = pts[i + 1]
        lo = min(a, b); hi = max(a, b)
        if not filled:
            if d < 0 and lo - hs <= E:
                filled = True
                # after filling on a down-leg, the rest of this leg is still down
                if b < a and b + hs <= TP:
                    return 1
                continue
            if d > 0 and hi + hs >= E:
                filled = True
                if b > a and b - hs >= TP:
                    return 1
                continue
            continue
        if d < 0:
            if b > a and hi + hs >= SL:
                return -1
            if b < a and lo + hs <= TP:
                return 1
        else:
            if b < a and lo - hs <= SL:
                return -1
            if b > a and hi - hs >= TP:
                return 1
    return 0
