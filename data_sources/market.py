"""
Descarga precios históricos y calcula volatilidad para Monte Carlo.
Fuente: Yahoo Finance (gratuita, sin API key). Para uso en cuenta real de
fondeo, sustituye por un feed de tu broker (MT5 API) para precios exactos.
"""
import yfinance as yf
import numpy as np


def get_price_history(ticker: str, period: str = "6mo", interval: str = "1d"):
    """Devuelve DataFrame con histórico de precios."""
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    return data


def compute_daily_returns(data):
    """Retornos logarítmicos diarios."""
    close = data["Close"].dropna()
    returns = np.log(close / close.shift(1)).dropna()
    return returns


def compute_volatility_stats(ticker: str):
    """
    Devuelve dict con:
    - last_price
    - daily_return_pct (último cambio %)
    - volatility_annualized_pct
    - mean_return (para Monte Carlo)
    - std_return (para Monte Carlo)
    """
    data = get_price_history(ticker)
    if data.empty or len(data) < 10:
        return None

    returns = compute_daily_returns(data)
    last_price = float(data["Close"].iloc[-1])
    prev_price = float(data["Close"].iloc[-2])
    daily_return_pct = (last_price / prev_price - 1) * 100

    mean_return = float(returns.mean())
    std_return = float(returns.std())
    volatility_annualized_pct = std_return * np.sqrt(252) * 100

    return {
        "last_price": last_price,
        "daily_return_pct": daily_return_pct,
        "volatility_annualized_pct": volatility_annualized_pct,
        "mean_return": mean_return,
        "std_return": std_return,
    }
