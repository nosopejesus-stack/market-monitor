"""
Orquestador principal.

Modos:
  python main.py --mode daily   -> informe completo (llamar 1x/día, ej. 7am)
  python main.py --mode alert   -> solo activos con señal fuerte + evento
                                    de alto impacto (llamar cada 15-30 min)
"""
import argparse
import sys

from config import (
    ASSETS, NEWS_KEYWORDS, HIGH_VOL_THRESHOLD,
    MC_SIMULATIONS, MC_HORIZON_DAYS, CALENDAR_MIN_IMPACT,
)
from data_sources.market import compute_volatility_stats
from data_sources.news import fetch_news_for_keywords, summarize_sentiment
from data_sources.calendar import get_high_impact_events
from analysis.monte_carlo import run_monte_carlo
from analysis.scoring import score_asset
from report.build_report import build_asset_block, build_full_report
from report.send_email import send_email_report

# Umbral de confianza para que un activo aparezca en modo "alert"
ALERT_CONFIDENCE_THRESHOLD = 60


def analyze_all_assets():
    """Ejecuta el pipeline completo para todos los activos configurados."""
    high_impact_events = get_high_impact_events(CALENDAR_MIN_IMPACT)
    results = []

    for ticker, name in ASSETS.items():
        stats = compute_volatility_stats(ticker)
        if stats is None:
            print(f"[main] sin datos para {name}, se omite.")
            continue

        mc = run_monte_carlo(
            last_price=stats["last_price"],
            mean_return=stats["mean_return"],
            std_return=stats["std_return"],
            days=MC_HORIZON_DAYS,
            simulations=MC_SIMULATIONS,
        )
        mc["last_price"] = stats["last_price"]

        keywords = NEWS_KEYWORDS.get(name, [name])
        news_items = fetch_news_for_keywords(keywords)
        sentiment = summarize_sentiment(news_items)

        score = score_asset(
            mc_result=mc,
            news_sentiment=sentiment,
            volatility_pct=stats["volatility_annualized_pct"],
            high_vol_threshold=HIGH_VOL_THRESHOLD,
        )

        asset_events = [e for e in high_impact_events if e["country"] in name or True]

        results.append({
            "name": name,
            "mc": mc,
            "score": score,
            "news": news_items,
            "events": asset_events[:2],
        })

    return results


def run_daily():
    results = analyze_all_assets()
    blocks = [
        build_asset_block(r["name"], r["mc"], r["score"], r["news"], r["events"])
        for r in results
    ]
    html = build_full_report(blocks, title="📊 Informe diario de mercado")
    send_email_report("📊 Informe diario de mercado - FTMO", html)


def run_alert_check():
    results = analyze_all_assets()
    urgent = [
        r for r in results
        if r["score"]["confidence_pct"] >= ALERT_CONFIDENCE_THRESHOLD
        and r["score"]["direction"] != "NEUTRAL"
    ]
    if not urgent:
        print("[main] sin alertas relevantes en este ciclo.")
        return

    blocks = [
        build_asset_block(r["name"], r["mc"], r["score"], r["news"], r["events"])
        for r in urgent
    ]
    html = build_full_report(blocks, title="🚨 Alerta de mercado")
    send_email_report(f"🚨 Alerta de mercado: {len(urgent)} activo(s) con señal fuerte", html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "alert"], default="daily")
    args = parser.parse_args()

    if args.mode == "daily":
        run_daily()
    else:
        run_alert_check()

    sys.exit(0)
