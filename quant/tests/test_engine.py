"""Hand-checked scenarios for the stop-order simulator. Run: python -m pytest quant/tests"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xau.engine import simulate, WORST, PATH, BEST, OUT_TP, OUT_SL, OUT_NOFILL, OUT_OPEN  # noqa: E402


def run(bars, closes, mode=PATH, spread=0.0, expiry=1, direction=-1, off=7.0, tp=7.0, sl=16.0):
    bars = np.array(bars, float)
    n = len(closes)
    # one bar per day
    start = np.arange(n); end = start + 1
    arr = lambda v: np.full(n, v, float)  # noqa: E731
    return simulate(bars, start, end, np.array(closes, float), direction, arr(off), arr(tp), arr(sl),
                    spread, expiry, 0, mode)


def test_short_tp():
    # day0 close 100 -> sell stop 93, TP 86, SL 109. day1 drops to 85.
    out, pnl, _, _ = run([[99, 101, 98, 100], [99, 99.5, 85, 86]], [100, 86])
    assert out[0] == OUT_TP and np.isclose(pnl[0], 7.0)


def test_short_no_fill():
    out, _, _, _ = run([[99, 101, 98, 100], [100, 104, 95, 103]], [100, 103])
    assert out[0] == OUT_NOFILL


def test_short_sl():
    out, pnl, _, _ = run([[99, 101, 98, 100], [100, 100, 92, 95], [95, 110, 94, 108]], [100, 95, 108])
    assert out[0] == OUT_SL and np.isclose(pnl[0], -16.0)


def test_ambiguous_bar_bounds():
    # fill bar spans both TP (86) and SL (109); bearish bar -> path O-H-L-C: high first (before fill) then low -> TP
    bars = [[99, 101, 98, 100], [100, 112, 80, 90]]
    assert run(bars, [100, 90], mode=WORST)[0][0] == OUT_SL
    assert run(bars, [100, 90], mode=BEST)[0][0] == OUT_TP
    assert run(bars, [100, 90], mode=PATH)[0][0] == OUT_TP
    # bullish bar O-L-H-C: drop fills and hits TP on the way down first
    bars2 = [[99, 101, 98, 100], [100, 112, 80, 111]]
    assert run(bars2, [100, 111], mode=PATH)[0][0] == OUT_TP


def test_path_fill_then_sl():
    # bullish bar O-L-H-C: low 92 fills at 93 (TP 86 not reached), then high 110 >= SL 109
    bars = [[99, 101, 98, 100], [100, 110, 92, 105]]
    out, pnl, _, _ = run(bars, [100, 105], mode=PATH)
    assert out[0] == OUT_SL and np.isclose(pnl[0], -16.0)
    # bearish bar O-H-L-C: high first (not filled yet), then low fills; no exit -> still open at end
    bars = [[99, 101, 98, 100], [100, 110, 92, 95]]
    assert run(bars, [100, 95], mode=PATH)[0][0] == OUT_OPEN
    assert run(bars, [100, 95], mode=BEST)[0][0] == OUT_OPEN
    assert run(bars, [100, 95], mode=WORST)[0][0] == OUT_SL


def test_gap_fill_worse_price():
    # day1 opens at 90, below the 93 sell stop -> fill at 90; TP stays at 86
    out, pnl, eb, _ = run([[99, 101, 98, 100], [90, 91, 85, 86]], [100, 86])
    assert out[0] == OUT_TP and np.isclose(pnl[0], 4.0)


def test_expiry():
    # no fill on day1, fill on day2: counts only with expiry >= 2
    bars = [[99, 101, 98, 100], [100, 101, 95, 100], [100, 100, 80, 81]]
    assert run(bars, [100, 100, 81], expiry=1)[0][0] == OUT_NOFILL
    assert run(bars, [100, 100, 81], expiry=2)[0][0] == OUT_TP


def test_spread_makes_tp_harder():
    # low exactly at TP 86: hit with zero spread, missed with spread 0.5 (ask = mid + 0.25)
    bars = [[99, 101, 98, 100], [99, 99.5, 86, 87]]
    assert run(bars, [100, 87], spread=0.0)[0][0] == OUT_TP
    assert run(bars, [100, 87], spread=0.5)[0][0] == OUT_OPEN


def test_buy_stop_mirror():
    out, pnl, _, _ = run([[99, 101, 98, 100], [101, 115, 100, 114]], [100, 114], direction=1)
    assert out[0] == OUT_TP and np.isclose(pnl[0], 7.0)
