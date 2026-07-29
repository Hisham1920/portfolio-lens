import unittest
from unittest.mock import patch

from app import app
from sample_data import DEMO_HOLDINGS
from services.portfolio_analyser import analyse_portfolio
from services.report_generator import WrittenPortfolioReport, build_report_pdf


class PortfolioReportTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.analysis = analyse_portfolio(DEMO_HOLDINGS)

    def test_automated_report_is_included_in_analysis(self):
        report = self.analysis["automated_report"]

        self.assertIn("executive_summary", report)
        self.assertGreaterEqual(len(report["sections"]), 4)
        self.assertTrue(report["strengths"])
        self.assertTrue(report["watch_items"])

    def test_pdf_builder_creates_valid_pdf_bytes(self):
        report = WrittenPortfolioReport.model_validate(
            self.analysis["automated_report"]
        ).model_dump()
        pdf = build_report_pdf(
            report,
            self.analysis["summary"],
            self.analysis["meta"]["portfolio_name"],
            "Automated Portfolio Report",
        )

        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 3000)

    def test_ai_report_route_requires_consent(self):
        response = self.client.post(
            "/api/portfolio/report/ai",
            json={"portfolio_name": "Test", "holdings": DEMO_HOLDINGS},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Consent", response.get_json()["error"])

    @patch("app.generate_ai_report")
    def test_ai_report_route_returns_structured_report(self, generate_mock):
        generate_mock.return_value = {
            "report": self.analysis["automated_report"],
            "model": "gpt-5.6-luna",
            "generated_at": "2026-07-27T00:00:00+00:00",
        }
        response = self.client.post(
            "/api/portfolio/report/ai",
            json={
                "portfolio_name": "Test Portfolio",
                "holdings": DEMO_HOLDINGS,
                "consent": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["model"], "gpt-5.6-luna")

    def test_pdf_route_downloads_report(self):
        response = self.client.post(
            "/api/portfolio/report/pdf",
            json={
                "portfolio_name": "Test Portfolio",
                "holdings": DEMO_HOLDINGS,
                "report": self.analysis["automated_report"],
                "report_label": "Automated Portfolio Report",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
