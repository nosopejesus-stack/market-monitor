# Quant lab

- `xau/data.py`: loading, timezone fix (Twelve Data H1 is Australia/Sydney time), MT5-style NY-17:00 daily bars
- `xau/engine.py`: numba event simulator for stop entries with TP/SL, spread, gaps, and WORST/PATH/BEST intrabar bounds
- `xau/features.py`: daily features known at the close (no look-ahead)
- `xau/study.py`: the full falsification battery (T1-T9) → `results/xau_study.md|json`
- `REPORT_XAUUSD.md`: the written verdict (EXP-001: killed)

## Data (not committed; provider terms)
Pull XAU/USD from Twelve Data (free plan: 8 credits/min, 800/day):
- `1day`, outputsize 5000, end_date today, plus a second call ending where the first stops (back to 1995)
- `1h`, outputsize 5000, in windows ending at successive dates back to 2020-01-24 (≈9 calls; each covers ~7-10 months)

Save each raw response (`{"result": "datetime;open;high;low;close\n..."}`) into one folder, then:
```bash
python quant/scripts/assemble_data.py <folder>   # writes quant/data/xauusd_d1.csv and xauusd_h1.csv
cd quant && python -m xau.study
```
The assembly script reports gaps longer than 5 days; fill them before running the study.
