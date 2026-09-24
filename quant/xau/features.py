"""Daily features known at the close of day t (no look-ahead)."""
import numpy as np
import pandas as pd


def daily_features(d: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=d.index)
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    prev_c = c.shift()
    tr = np.maximum(h - l, np.maximum((h - prev_c).abs(), (l - prev_c).abs()))
    f["atr14"] = tr.rolling(14).mean()
    f["atr100"] = tr.rolling(100).mean()
    rng = (h - l).replace(0, np.nan)
    f["bull"] = c > o
    f["bear"] = c < o
    f["body_atr"] = (c - o).abs() / f["atr14"]
    f["upper_wick_frac"] = (h - np.maximum(o, c)) / rng
    f["lower_wick_frac"] = (np.minimum(o, c) - l) / rng
    f["close_pos"] = (c - l) / rng  # 1 = closed at high
    # consecutive bullish closes ending at t
    run = np.zeros(len(d), int)
    b = f["bull"].to_numpy()
    for i in range(len(d)):
        run[i] = run[i - 1] + 1 if (b[i] and i > 0) else (1 if b[i] else 0)
    f["bull_run"] = run
    sma10 = c.rolling(10).mean()
    f["sma50"] = c.rolling(50).mean()
    f["sma200"] = c.rolling(200).mean()
    f["uptrend"] = (c > f["sma200"]) & (f["sma50"] > f["sma200"])
    f["downtrend"] = (c < f["sma200"]) & (f["sma50"] < f["sma200"])
    sma20 = c.rolling(20).mean()
    f["trend_strength"] = (sma20 - sma20.shift(10)).abs() / f["atr14"]
    f["dist_high20_atr"] = (h.rolling(20).max() - c) / f["atr14"]
    f["dist_low20_atr"] = (c - l.rolling(20).min()) / f["atr14"]
    f["vol_regime"] = f["atr14"] / f["atr100"]
    # "two large bullish recovery candles": two bullish days, each body >= 0.6 ATR,
    # starting from below the 10-day average (i.e. recovering from weakness).
    large = f["bull"] & (f["body_atr"] >= 0.6)
    f["two_large_recovery"] = large & large.shift(1, fill_value=False) & (c.shift(2) < sma10.shift(2))
    f["weekday"] = d.index.dayofweek
    nxt = pd.Series(d.index, index=d.index).shift(-1)
    # APPROXIMATION: US payrolls are usually released on the first Friday of the month.
    f["next_day_nfp_proxy"] = (nxt.dt.dayofweek == 4) & (nxt.dt.day <= 7)
    return f
