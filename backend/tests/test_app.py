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


if __name__ == "__main__":
    unittest.main()
