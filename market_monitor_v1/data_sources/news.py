"""
Descarga noticias vía NewsAPI (https://newsapi.org, tiene tier gratuito
100 requests/día) y aplica un análisis de sentimiento simple con TextBlob.

Requiere variable de entorno NEWSAPI_KEY (gratis, registro en 2 min).
"""
import os
import requests
from textblob import TextBlob

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_news_for_keywords(keywords: list[str], max_results: int = 5):
    """Busca noticias recientes que contengan alguna de las keywords."""
    if not NEWSAPI_KEY:
        return []

    query = " OR ".join(keywords)
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": NEWSAPI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception as e:
        print(f"[news] error fetching news: {e}")
        return []

    results = []
    for a in articles:
        title = a.get("title") or ""
        description = a.get("description") or ""
        text = f"{title}. {description}"
        sentiment = TextBlob(text).sentiment.polarity  # -1 (negativo) a +1 (positivo)
        results.append({
            "title": title,
            "url": a.get("url"),
            "source": a.get("source", {}).get("name"),
            "published_at": a.get("publishedAt"),
            "sentiment": sentiment,
        })
    return results


def summarize_sentiment(news_items: list[dict]) -> float:
    """Devuelve sentimiento medio (-1 a +1) de una lista de noticias."""
    if not news_items:
        return 0.0
    return sum(n["sentiment"] for n in news_items) / len(news_items)
