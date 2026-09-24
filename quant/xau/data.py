"""Data loading for the XAUUSD study.

Facts established empirically (see experiments/EXP-001):
- Twelve Data H1 XAU/USD timestamps are in Australia/Sydney local time: the daily
  maintenance gap sits at 07:00/08:00/09:00 local depending on US/AU DST, which is
  exactly 17:00 America/New_York all year.
- Native Twelve Data D1 bars before 2006 have implausibly small ranges (fixing
  prices, not OHLC) and are excluded. Native D1 in 2024+ contains weekend stubs.

Broker-style daily bars ("MT5 server day", NY 17:00 -> 17:00) are rebuilt from H1
for 2020+. Native D1 (2006-2019) is used only for the long-history daily-bar test.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
H1_TZ = "Australia/Sydney"


def load_h1() -> pd.DataFrame:
    h = pd.read_csv(DATA / "xauusd_h1.csv", parse_dates=["datetime"])
    local = h["datetime"].dt.tz_localize(H1_TZ, ambiguous="NaT", nonexistent="NaT")
    h = h[local.notna()].copy()
    h["ny"] = local[local.notna()].dt.tz_convert("America/New_York").dt.tz_localize(None)
    # MT5-style server day: NY 17:00 starts the next trading day.
    h["day"] = (h["ny"] + pd.Timedelta(hours=7)).dt.normalize()
    h = h.sort_values("ny").drop_duplicates("ny").reset_index(drop=True)
    return h[["ny", "day", "open", "high", "low", "close"]]


def build_broker_d1(h1: pd.DataFrame) -> pd.DataFrame:
    g = h1.groupby("day")
    d = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(),
        "low": g["low"].min(), "close": g["close"].last(), "nbars": g.size(),
    })
    # Weekend stubs (a few bars stamped on Sat/Sun server days) are folded away:
    # keep Mon-Fri only; drop the partial first day of the series.
    d = d[d.index.dayofweek < 5]
    d = d[d["nbars"] >= 10]
    return d.iloc[1:]


def load_native_d1(start="2006-01-01", end="2019-12-31") -> pd.DataFrame:
    d = pd.read_csv(DATA / "xauusd_d1.csv", parse_dates=["datetime"]).set_index("datetime")
    d = d[(d.index >= start) & (d.index <= end) & (d.index.dayofweek < 5)]
    d = d[d["high"] > d["low"]]
    return d[["open", "high", "low", "close"]]


def bar_arrays_from_h1(h1: pd.DataFrame, d1: pd.DataFrame):
    """Return (bars ndarray [n,4] o/h/l/c, day_start, day_end) aligned to d1 rows."""
    h = h1[h1["day"].isin(d1.index)].reset_index(drop=True)
    bars = h[["open", "high", "low", "close"]].to_numpy(float)
    pos = {day: i for i, day in enumerate(d1.index)}
    di = h["day"].map(pos).to_numpy()
    start = np.searchsorted(di, np.arange(len(d1)), side="left")
    end = np.searchsorted(di, np.arange(len(d1)), side="right")
    return bars, start, end


def bar_arrays_from_d1(d1: pd.DataFrame):
    bars = d1[["open", "high", "low", "close"]].to_numpy(float)
    idx = np.arange(len(d1))
    return bars, idx, idx + 1
