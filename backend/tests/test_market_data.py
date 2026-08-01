import unittest
from unittest.mock import patch

from services.market_data import (
    SymbolReviewRequired,
    clear_price_cache,
    normalise_nse_symbol,
    refresh_holdings_prices,
    yahoo_ticker,
)


HOLDINGS = [
    {
        "symbol": "RELIANCE",
        "company": "Reliance Industries",
        "quantity": 2,
        "average_price": 1200,
        "current_price": 1300,
        "sector": "Energy",
        "market_cap": "Large Cap",
    },
    {
        "symbol": "UNKNOWN",
        "company": "Unknown",
        "quantity": 1,
        "average_price": 100,
        "current_price": 95,
        "sector": "Other",
        "market_cap": "Small Cap",
    },
]


class MarketDataTest(unittest.TestCase):
    def setUp(self):
        clear_price_cache()

    def test_normalises_nse_symbols(self):
        self.assertEqual(normalise_nse_symbol(" reliance.ns "), "RELIANCE")
        self.assertEqual(normalise_nse_symbol("NSE:RELIANCE"), "RELIANCE")
        self.assertEqual(normalise_nse_symbol("NSE_EQ|RELIANCE"), "RELIANCE")
        self.assertEqual(normalise_nse_symbol("RELIANCE-EQ"), "RELIANCE")
        self.assertEqual(yahoo_ticker("M&M"), "M&M.NS")

    def test_flags_old_tata_motors_symbol_for_corporate_action_review(self):
        with self.assertRaises(SymbolReviewRequired) as context:
            yahoo_ticker("TATAMOTORS")

        self.assertEqual(context.exception.suggested_symbols, ["TMPV", "TMCV"])

    @patch("services.market_data._fetch_yahoo_quote")
    def test_refreshes_available_prices_and_preserves_failed_prices(self, fetch_mock):
        def quote(ticker):
            if ticker == "UNKNOWN.NS":
                raise ValueError("Unsupported test symbol.")
            return {
                "ticker": ticker,
                "price": 1475.25,
                "currency": "INR",
                "exchange": "NSE",
                "market_time": "2026-07-29T08:30:00+00:00",
            }

        fetch_mock.side_effect = quote

        refreshed, meta = refresh_holdings_prices(HOLDINGS)

        self.assertEqual(refreshed[0]["current_price"], 1475.25)
        self.assertEqual(refreshed[0]["price_source"], "Yahoo Finance")
        self.assertEqual(refreshed[1]["current_price"], 95)
        self.assertEqual(meta["refreshed_symbols"], ["RELIANCE"])
        self.assertEqual(meta["failed_count"], 1)

    @patch("services.market_data._fetch_yahoo_quote")
    def test_corporate_action_failure_includes_suggestions(self, fetch_mock):
        fetch_mock.return_value = {
            "ticker": "RELIANCE.NS",
            "price": 1475.25,
            "currency": "INR",
            "exchange": "NSE",
            "market_time": "2026-07-29T08:30:00+00:00",
        }
        holdings = [HOLDINGS[0], {**HOLDINGS[1], "symbol": "TATAMOTORS"}]

        _, meta = refresh_holdings_prices(holdings)

        failure = meta["failed_symbols"][0]
        self.assertEqual(failure["symbol"], "TATAMOTORS")
        self.assertEqual(failure["type"], "corporate_action_review")
        self.assertEqual(failure["suggested_symbols"], ["TMPV", "TMCV"])

    @patch("services.market_data._fetch_yahoo_quote")
    def test_uses_cache_on_second_refresh(self, fetch_mock):
        fetch_mock.return_value = {
            "ticker": "RELIANCE.NS",
            "price": 1475.25,
            "currency": "INR",
            "exchange": "NSE",
            "market_time": "2026-07-29T08:30:00+00:00",
        }
        one_holding = [HOLDINGS[0]]

        _, first_meta = refresh_holdings_prices(one_holding)
        _, second_meta = refresh_holdings_prices(one_holding)

        self.assertEqual(fetch_mock.call_count, 1)
        self.assertEqual(first_meta["cache_hits"], 0)
        self.assertEqual(second_meta["cache_hits"], 1)


if __name__ == "__main__":
    unittest.main()
