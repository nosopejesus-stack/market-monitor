import csv
import os
import unittest
from datetime import datetime, timezone
from unittest import mock

import main
from analysis.scoring import score_asset
from data_sources import calendar, market

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "eurusd_1day.csv")


def load_fixture_values():
    """Serie diaria real de EUR/USD de Twelve Data (orden más reciente primero, como la API)."""
    with open(FIXTURE) as f:
        return list(csv.DictReader(f, delimiter=";"))


class MarketTests(unittest.TestCase):
    def test_parse_sorts_oldest_first(self):
        closes = market.parse_twelvedata_values(load_fixture_values())
        self.assertEqual(len(closes), 90)
        self.assertAlmostEqual(closes[0], 1.13786)   # 2026-07-01
        self.assertAlmostEqual(closes[-1], 1.13703)  # 2026-09-28

    def test_stats_from_real_series(self):
        stats = market.compute_stats_from_closes(
            market.parse_twelvedata_values(load_fixture_values()))
        self.assertAlmostEqual(stats["last_price"], 1.13703)
        self.assertAlmostEqual(stats["daily_return_pct"], (1.13703 / 1.13832 - 1) * 100)
        # EUR/USD: volatilidad diaria típica bien por debajo del 1 %
        self.assertTrue(0.05 < stats["daily_volatility_pct"] < 1.0)

    def test_too_few_points_returns_none(self):
        self.assertIsNone(market.compute_stats_from_closes([1.0] * 5))
        self.assertIsNone(market.compute_stats_from_closes(None))

    def test_falls_back_to_yahoo(self):
        closes = market.parse_twelvedata_values(load_fixture_values())
        with mock.patch.object(market, "fetch_closes_twelvedata", return_value=None), \
             mock.patch.object(market, "fetch_closes_yahoo", return_value=closes) as yahoo:
            out = market.get_closes({"twelvedata": "EUR/USD", "yahoo": "EURUSD=X"})
        yahoo.assert_called_once_with("EURUSD=X")
        self.assertEqual(len(out), 90)

    def test_twelvedata_error_payload(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {"status": "error", "code": 429, "message": "limit"}
        with mock.patch.object(market, "TWELVEDATA_API_KEY", "k"), \
             mock.patch.object(market, "TWELVEDATA_MIN_INTERVAL_S", 0), \
             mock.patch.object(market.requests, "get", return_value=resp):
            self.assertIsNone(market.fetch_closes_twelvedata("EUR/USD"))


class CalendarTests(unittest.TestCase):
    NOW = datetime(2026, 9, 28, 5, 0, tzinfo=timezone.utc)
    EVENTS = [
        {"title": "CPI", "country": "USD", "date": "2026-09-28T08:30:00-04:00", "impact": "High"},
        {"title": "ECB", "country": "EUR", "date": "2026-09-28T12:15:00+00:00", "impact": "High"},
        {"title": "Old", "country": "USD", "date": "2026-09-25T08:30:00-04:00", "impact": "High"},
        {"title": "Later", "country": "USD", "date": "2026-10-01T08:30:00-04:00", "impact": "High"},
        {"title": "Minor", "country": "USD", "date": "2026-09-28T09:00:00-04:00", "impact": "Low"},
    ]

    def test_only_next_24h_high_impact(self):
        out = calendar.filter_events(self.EVENTS, 3, 24, now=self.NOW)
        self.assertEqual([e["title"] for e in out], ["ECB", "CPI"])

    def test_events_per_currency(self):
        out = calendar.filter_events(self.EVENTS, 3, 24, now=self.NOW)
        self.assertEqual([e["title"] for e in calendar.events_for_currencies(out, ["JPY"])], [])
        self.assertEqual([e["title"] for e in calendar.events_for_currencies(out, ["EUR"])], ["ECB"])


class ScoringTests(unittest.TestCase):
    MC = {"prob_up": 60, "prob_down": 40, "expected_move_pct": 0.1}

    def test_high_daily_vol_reduces_confidence(self):
        calm = score_asset(self.MC, 0.0, volatility_pct=0.4, high_vol_threshold=1.2)
        wild = score_asset(self.MC, 0.0, volatility_pct=2.5, high_vol_threshold=1.2)
        self.assertEqual(calm["confidence_pct"], 10.0)
        self.assertEqual(wild["confidence_pct"], 8.0)
        self.assertIn("Volatilidad diaria alta", wild["reasoning"])


class PipelineTests(unittest.TestCase):
    def test_daily_report_end_to_end(self):
        closes = market.parse_twelvedata_values(load_fixture_values())
        events = calendar.filter_events(CalendarTests.EVENTS, 3, 24, now=CalendarTests.NOW)
        news = [{"title": "Euro <rallies>", "url": "https://x/?a=1&b=2",
                 "source": "Test", "published_at": None, "sentiment": 0.3}]
        sent = {}
        with mock.patch("data_sources.market.get_closes", return_value=closes), \
             mock.patch.object(main, "get_high_impact_events", return_value=events), \
             mock.patch.object(main, "fetch_news_for_keywords", return_value=news), \
             mock.patch.object(main, "send_email_report",
                               side_effect=lambda subj, html: sent.update(subj=subj, html=html)):
            main.run_daily()

        html = sent["html"]
        self.assertEqual(html.count("<h3"), len(main.ASSETS))
        self.assertIn("Euro &lt;rallies&gt;", html)
        self.assertIn("ECB", html)                 # evento EUR en el bloque EUR/USD
        usd_jpy_block = html.split("USD/JPY")[1].split("<h3")[0]
        self.assertNotIn("ECB", usd_jpy_block)     # pero no en USD/JPY


if __name__ == "__main__":
    unittest.main()
