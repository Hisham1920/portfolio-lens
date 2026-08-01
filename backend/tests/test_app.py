import io
import unittest
from unittest.mock import patch

from app import app


class PortfolioExtractionRouteTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_requires_explicit_consent(self):
        response = self.client.post(
            "/api/portfolio/extract",
            data={"files": (io.BytesIO(b"\x89PNG\r\n\x1a\nimage"), "portfolio.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Consent", response.get_json()["error"])

    @patch("app.extract_portfolio_documents")
    def test_returns_extracted_holdings(self, extract_mock):
        extract_mock.return_value = {
            "broker": "Upstox",
            "holdings": [
                {
                    "symbol": "CDSL",
                    "company": "CDSL",
                    "quantity": 20,
                    "average_price": 1764.30,
                    "current_price": 1173.25,
                    "sector": "Financials",
                    "market_cap": "Mid Cap",
                    "confidence": 0.98,
                    "warning": "",
                    "source_file": "upstox.png",
                },
                {
                    "symbol": "IRCON",
                    "company": "IRCON",
                    "quantity": 100,
                    "average_price": 234.33,
                    "current_price": 155.42,
                    "sector": "Industrials",
                    "market_cap": "Mid Cap",
                    "confidence": 0.98,
                    "warning": "",
                    "source_file": "upstox.png",
                },
            ],
            "warnings": [],
            "source_count": 1,
            "model": "gpt-5.6",
        }

        response = self.client.post(
            "/api/portfolio/extract",
            data={
                "consent": "true",
                "files": (io.BytesIO(b"\x89PNG\r\n\x1a\nimage"), "upstox.png"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["broker"], "Upstox")
        self.assertEqual([item["symbol"] for item in payload["holdings"]], ["CDSL", "IRCON"])

    @patch("app.refresh_holdings_prices")
    def test_refreshes_prices_and_recalculates_portfolio(self, refresh_mock):
        refreshed_holding = {
            "symbol": "RELIANCE",
            "company": "Reliance Industries",
            "quantity": 2,
            "average_price": 1200,
            "current_price": 1500,
            "sector": "Energy",
            "market_cap": "Large Cap",
        }
        refresh_mock.return_value = (
            [refreshed_holding],
            {
                "provider": "Yahoo Finance",
                "price_type": "latest_available_snapshot",
                "fetched_at": "2026-07-29T08:30:00+00:00",
                "may_be_delayed": True,
                "refreshed_symbols": ["RELIANCE"],
                "failed_symbols": [],
                "refreshed_count": 1,
                "failed_count": 0,
                "cache_hits": 0,
                "cache_ttl_seconds": 300,
                "provider_code": "yahoo_chart",
            },
        )

        response = self.client.post(
            "/api/portfolio/refresh-prices",
            json={"portfolio_name": "Test Portfolio", "holdings": [refreshed_holding]},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["holdings"][0]["current_price"], 1500)
        self.assertEqual(payload["meta"]["market_data"]["provider"], "Yahoo Finance")
        self.assertIn("may be delayed", payload["meta"]["data_notice"])

    def test_refresh_requires_holdings(self):
        response = self.client.post("/api/portfolio/refresh-prices", json={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("non-empty", response.get_json()["error"])

    def test_accepts_alternate_local_vite_port(self):
        response = self.client.get(
            "/api/health",
            headers={"Origin": "http://localhost:5174"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:5174",
        )


if __name__ == "__main__":
    unittest.main()
