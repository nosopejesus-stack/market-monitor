"""
Simulación Monte Carlo (movimiento browniano geométrico) para estimar
la probabilidad de que un activo suba o baje en el próximo horizonte.
"""
import numpy as np


def run_monte_carlo(last_price, mean_return, std_return, days=1, simulations=5000):
    """
    Devuelve:
    - prob_up: probabilidad (%) de que el precio final sea mayor al actual
    - prob_down: probabilidad (%) de que sea menor
    - expected_move_pct: movimiento medio esperado (%)
    - p5, p95: percentiles 5 y 95 del precio simulado (rango de confianza)
    """
    rng = np.random.default_rng()
    daily_shocks = rng.normal(mean_return, std_return, size=(simulations, days))
    cumulative_returns = daily_shocks.sum(axis=1)
    final_prices = last_price * np.exp(cumulative_returns)

    prob_up = float((final_prices > last_price).mean() * 100)
    prob_down = float((final_prices < last_price).mean() * 100)
    expected_move_pct = float((final_prices.mean() / last_price - 1) * 100)
    p5 = float(np.percentile(final_prices, 5))
    p95 = float(np.percentile(final_prices, 95))

    return {
        "prob_up": prob_up,
        "prob_down": prob_down,
        "expected_move_pct": expected_move_pct,
        "p5": p5,
        "p95": p95,
    }
