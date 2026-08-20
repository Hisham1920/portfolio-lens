import unittest

from services.corporate_actions import (
    CorporateActionError,
    resolve_tata_motors_demerger,
)


LEGACY_HOLDING = {
    "symbol": "TATAMOTORS",
    "company": "Tata Motors",
    "quantity": 30,
    "average_price": 868,
    "current_price": 812.35,
    "sector": "Automobile",
    "market_cap": "Large Cap",
}


class CorporateActionTest(unittest.TestCase):
    def test_requires_record_date_confirmation(self):
        with self.assertRaises(CorporateActionError):
            resolve_tata_motors_demerger([LEGACY_HOLDING])

    def test_splits_quantity_and_allocates_cost_basis(self):
        resolved, meta = resolve_tata_motors_demerger(
            [LEGACY_HOLDING],
            held_on_record_date=True,
        )

        self.assertEqual([item["symbol"] for item in resolved], ["TMPV", "TMCV"])
        self.assertEqual([item["quantity"] for item in resolved], [30, 30])
        self.assertAlmostEqual(resolved[0]["average_price"], 597.618, places=3)
        self.assertAlmostEqual(resolved[1]["average_price"], 270.382, places=3)
        self.assertAlmostEqual(
            sum(item["quantity"] * item["average_price"] for item in resolved),
            LEGACY_HOLDING["quantity"] * LEGACY_HOLDING["average_price"],
            places=2,
        )
        self.assertEqual(meta["cost_allocation"], {"TMPV": 68.85, "TMCV": 31.15})

    def test_preserves_non_legacy_holdings(self):
        reliance = {**LEGACY_HOLDING, "symbol": "RELIANCE", "company": "Reliance"}
        resolved, _ = resolve_tata_motors_demerger(
            [reliance, LEGACY_HOLDING],
            held_on_record_date=True,
        )

        self.assertEqual([item["symbol"] for item in resolved], ["RELIANCE", "TMPV", "TMCV"])


if __name__ == "__main__":
    unittest.main()
