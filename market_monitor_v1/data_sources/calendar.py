"""
Calendario económico gratuito (ForexFactory, formato JSON público usado
por muchos bots). Sin API key. Puede fallar si cambia la URL; en ese caso
sustituir por Investing.com API o TradingEconomics (de pago, más fiable).
"""
import requests

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

IMPACT_MAP = {"Low": 1, "Medium": 2, "High": 3}


def fetch_weekly_calendar():
    try:
        resp = requests.get(CALENDAR_URL, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[calendar] error fetching calendar: {e}")
        return []


def get_high_impact_events(min_impact: int = 3):
    """Filtra eventos de hoy con impacto >= min_impact."""
    events = fetch_weekly_calendar()
    filtered = []
    for e in events:
        impact = IMPACT_MAP.get(e.get("impact", ""), 0)
        if impact >= min_impact:
            filtered.append({
                "title": e.get("title"),
                "country": e.get("country"),
                "date": e.get("date"),
                "impact": e.get("impact"),
                "forecast": e.get("forecast"),
                "previous": e.get("previous"),
            })
    return filtered
