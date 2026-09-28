"""
Descarga precios históricos y calcula volatilidad para Monte Carlo.

Fuente principal: Twelve Data (requiere variable de entorno TWELVEDATA_API_KEY;
plan gratuito: 800 créditos/día y 8 peticiones/minuto).
Respaldo: Yahoo Finance vía yfinance (gratis, sin key) si Twelve Data falla
o no hay key configurada.
"""
import os
import time

import numpy as np
import requests

TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
TWELVEDATA_URL = "https://api.twelvedata.com/time_series"

# Plan gratuito: 8 peticiones/minuto -> 1 petición cada 8 s como mínimo
TWELVEDATA_MIN_INTERVAL_S = 8.0
_last_twelvedata_call = 0.0

HISTORY_DAYS = 130  # ~6 meses de velas diarias


def parse_twelvedata_values(values: list[dict]) -> np.ndarray:
    """Convierte la lista 'values' de Twelve Data en cierres ordenados de antiguo a reciente."""
    rows = sorted(values, key=lambda v: v["datetime"])
    return np.array([float(v["close"]) for v in rows], dtype=float)


def _throttle():
    global _last_twelvedata_call
    wait = TWELVEDATA_MIN_INTERVAL_S - (time.monotonic() - _last_twelvedata_call)
    if wait > 0:
        time.sleep(wait)
    _last_twelvedata_call = time.monotonic()


def fetch_closes_twelvedata(symbol: str, outputsize: int = HISTORY_DAYS):
    if not TWELVEDATA_API_KEY:
        return None
    _throttle()
    params = {
        "symbol": symbol,
        "interval": "1day",
        "outputsize": outputsize,
        "apikey": TWELVEDATA_API_KEY,
    }
    try:
        resp = requests.get(TWELVEDATA_URL, params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"[market] error Twelve Data {symbol}: {e}")
        return None

    if payload.get("status") != "ok" or not payload.get("values"):
        print(f"[market] Twelve Data {symbol}: {payload.get('message', 'sin datos')}")
        return None
    return parse_twelvedata_values(payload["values"])


def fetch_closes_yahoo(ticker: str, period: str = "6mo"):
    try:
        import yfinance as yf
        data = yf.download(ticker, period=period, interval="1d", progress=False)
    except Exception as e:
        print(f"[market] error Yahoo {ticker}: {e}")
        return None
    if data is None or data.empty:
        return None
    # yfinance recientes devuelven columnas MultiIndex -> aplanar a 1D
    return data["Close"].to_numpy(dtype=float).ravel()


def get_closes(symbols: dict):
    """Cierres diarios (antiguo -> reciente) probando Twelve Data y luego Yahoo."""
    closes = None
    if symbols.get("twelvedata"):
        closes = fetch_closes_twelvedata(symbols["twelvedata"])
    if closes is None and symbols.get("yahoo"):
        closes = fetch_closes_yahoo(symbols["yahoo"])
    return closes


def compute_stats_from_closes(closes):
    """
    Devuelve dict con:
    - last_price
    - daily_return_pct (último cambio %)
    - daily_volatility_pct (desviación típica de retornos diarios, %)
    - volatility_annualized_pct
    - mean_return, std_return (retornos log diarios, para Monte Carlo)
    """
    if closes is None:
        return None
    closes = np.asarray(closes, dtype=float)
    closes = closes[~np.isnan(closes)]
    if len(closes) < 10:
        return None

    returns = np.diff(np.log(closes))
    last_price = float(closes[-1])
    prev_price = float(closes[-2])
    std_return = float(returns.std(ddof=1))

    return {
        "last_price": last_price,
        "daily_return_pct": (last_price / prev_price - 1) * 100,
        "daily_volatility_pct": std_return * 100,
        "volatility_annualized_pct": float(std_return * np.sqrt(252) * 100),
        "mean_return": float(returns.mean()),
        "std_return": std_return,
    }


def compute_volatility_stats(symbols: dict):
    return compute_stats_from_closes(get_closes(symbols))
