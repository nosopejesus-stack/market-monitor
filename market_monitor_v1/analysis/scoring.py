"""
Combina señales (Monte Carlo + sentimiento de noticias + eventos de
calendario) en un score direccional por activo.

IMPORTANTE: esto es un modelo heurístico de apoyo, no una predicción
garantizada. Los pesos son ajustables en config.py o aquí abajo.
"""

W_MONTE_CARLO = 0.5
W_NEWS_SENTIMENT = 0.3
W_VOLATILITY_PENALTY = 0.2


def score_asset(mc_result: dict, news_sentiment: float, volatility_pct: float, high_vol_threshold: float):
    """
    Devuelve dict con:
    - direction: "ALZA" | "BAJA" | "NEUTRAL"
    - confidence_pct: 0-100
    - reasoning: texto explicando el porqué
    """
    # Señal Monte Carlo normalizada a [-1, 1]
    mc_signal = (mc_result["prob_up"] - mc_result["prob_down"]) / 100

    # Señal de noticias ya está en [-1, 1] aprox
    news_signal = max(-1, min(1, news_sentiment * 2))

    combined = (mc_signal * W_MONTE_CARLO) + (news_signal * W_NEWS_SENTIMENT)

    # Penalización si hay alta volatilidad (mayor incertidumbre)
    is_high_vol = volatility_pct >= high_vol_threshold
    confidence = abs(combined) * 100
    if is_high_vol:
        confidence *= (1 - W_VOLATILITY_PENALTY)

    if combined > 0.08:
        direction = "ALZA"
    elif combined < -0.08:
        direction = "BAJA"
    else:
        direction = "NEUTRAL"

    reasoning_parts = [
        f"Monte Carlo: {mc_result['prob_up']:.1f}% prob. alza / {mc_result['prob_down']:.1f}% prob. baja",
        f"Movimiento esperado: {mc_result['expected_move_pct']:.2f}%",
        f"Sentimiento de noticias: {'positivo' if news_signal > 0.1 else 'negativo' if news_signal < -0.1 else 'neutral'}",
    ]
    if is_high_vol:
        reasoning_parts.append(f"⚠️ Volatilidad alta ({volatility_pct:.2f}%) → confianza reducida")

    return {
        "direction": direction,
        "confidence_pct": round(min(confidence, 99), 1),
        "reasoning": " | ".join(reasoning_parts),
    }
