"""
Calendario económico gratuito (ForexFactory, formato JSON público usado
por muchos bots). Sin API key. Puede fallar si cambia la URL; en ese caso
sustituir por Investing.com API o TradingEconomics (de pago, más fiable).
"""
from datetime import datetime, timedelta, timezone

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


def _parse_date(value):
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def filter_events(events, min_impact=3, lookahead_hours=24, now=None):
    """
    Eventos con impacto >= min_impact que ocurren entre hace 1 h y
    las próximas `lookahead_hours` horas, ordenados por fecha.
    """
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=lookahead_hours)

    filtered = []
    for e in events:
        if IMPACT_MAP.get(e.get("impact", ""), 0) < min_impact:
            continue
        when = _parse_date(e.get("date"))
        if when is None or not (start <= when <= end):
            continue
        filtered.append({
            "title": e.get("title"),
            "country": e.get("country"),
            "date": e.get("date"),
            "when": when,
            "impact": e.get("impact"),
            "forecast": e.get("forecast"),
            "previous": e.get("previous"),
        })
    return sorted(filtered, key=lambda e: e["when"])


def get_high_impact_events(min_impact: int = 3, lookahead_hours: int = 24):
    return filter_events(fetch_weekly_calendar(), min_impact, lookahead_hours)


def events_for_currencies(events, currencies):
    """ForexFactory usa la divisa en el campo 'country' (USD, EUR, ...)."""
    wanted = {c.upper() for c in currencies}
    return [e for e in events if (e.get("country") or "").upper() in wanted]
