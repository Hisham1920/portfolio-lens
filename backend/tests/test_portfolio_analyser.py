import unittest

from sample_data import DEMO_HOLDINGS
from services.portfolio_analyser import analyse_portfolio


class PortfolioAnalyserTest(unittest.TestCase):
    def test_summary_matches_holding_totals(self):
        result = analyse_portfolio(DEMO_HOLDINGS)
        expected_invested = sum(
            item["quantity"] * item["average_price"] for item in DEMO_HOLDINGS
        )
        expected_current = sum(
            item["quantity"] * item["current_price"] for item in DEMO_HOLDINGS
        )

        self.assertEqual(result["summary"]["invested_value"], round(expected_invested, 2))
        self.assertEqual(result["summary"]["current_value"], round(expected_current, 2))
        self.assertEqual(result["summary"]["holdings_count"], len(DEMO_HOLDINGS))

    def test_allocations_total_one_hundred_percent(self):
        result = analyse_portfolio(DEMO_HOLDINGS)
        sector_total = sum(item["percentage"] for item in result["sector_allocation"])
        market_cap_total = sum(item["percentage"] for item in result["market_cap_allocation"])

        self.assertAlmostEqual(sector_total, 100, places=1)
        self.assertAlmostEqual(market_cap_total, 100, places=1)

    def test_rejects_missing_required_field(self):
        invalid_holding = [{"symbol": "TEST"}]

        with self.assertRaises(KeyError):
            analyse_portfolio(invalid_holding)

    def test_custom_portfolio_metadata(self):
        result = analyse_portfolio(
            DEMO_HOLDINGS,
            portfolio_name="Hisham's Portfolio",
            data_notice="User supplied prices.",
        )

        self.assertEqual(result["meta"]["portfolio_name"], "Hisham's Portfolio")
        self.assertEqual(result["meta"]["data_notice"], "User supplied prices.")

    def test_deep_analytics_are_internally_consistent(self):
        result = analyse_portfolio(DEMO_HOLDINGS)
        summary = result["summary"]
        performance = result["performance"]

        self.assertGreaterEqual(summary["health_score"], 0)
        self.assertLessEqual(summary["health_score"], 100)
        self.assertLessEqual(summary["effective_holdings"], summary["holdings_count"])
        self.assertEqual(
            summary["winners_count"] + summary["losers_count"] + summary["flat_count"],
            summary["holdings_count"],
        )
        self.assertAlmostEqual(
            performance["profitable_weight"] + performance["loss_making_weight"],
            100,
            delta=0.2,
        )

    def test_return_contributions_sum_to_total_return(self):
        result = analyse_portfolio(DEMO_HOLDINGS)
        contribution = sum(item["return_contribution"] for item in result["holdings"])

        self.assertAlmostEqual(contribution, result["summary"]["total_return"], places=1)

    def test_stress_scenarios_reduce_value(self):
        result = analyse_portfolio(DEMO_HOLDINGS)

        self.assertEqual(len(result["stress_scenarios"]), 4)
        self.assertTrue(
            all(
                scenario["stressed_value"] < result["summary"]["current_value"]
                for scenario in result["stress_scenarios"]
            )
        )


if __name__ == "__main__":
    unittest.main()
