"""Assemble raw Twelve Data XAU/USD exports (JSON {result: 'csv;...'}) into clean CSVs.

Usage: python assemble_data.py <raw_dir>
Writes quant/data/xauusd_d1.csv and quant/data/xauusd_h1.csv (UTC timestamps, as delivered).
"""
import json
import sys
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data"


def load(path):
    raw = json.load(open(path))["result"].strip()
    if not raw.startswith("datetime"):
        return None
    rows = [l.split(";") for l in raw.split("\n")[1:] if l and l[0].isdigit()]
    df = pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)
    return df


def main(raw_dir):
    d1, h1 = [], []
    for p in sorted(Path(raw_dir).glob("mcp-Twelve_Data-get_time_series-*.txt")):
        df = load(p)
        if df is None:
            continue
        intraday = (df["datetime"].dt.hour != 0).any()
        (h1 if intraday else d1).append(df)
    for name, parts in [("xauusd_d1.csv", d1), ("xauusd_h1.csv", h1)]:
        df = pd.concat(parts).drop_duplicates("datetime").sort_values("datetime").reset_index(drop=True)
        df.to_csv(OUT / name, index=False)
        gaps = df["datetime"].diff().dt.days.gt(5).sum()
        print(f"{name}: {len(df)} rows {df.datetime.min()} -> {df.datetime.max()}, gaps>5d: {gaps}")


if __name__ == "__main__":
    main(sys.argv[1])
