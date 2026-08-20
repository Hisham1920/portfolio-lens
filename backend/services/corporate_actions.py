from copy import deepcopy


class CorporateActionError(ValueError):
    pass


TATA_MOTORS_DEMERGER = {
    "legacy_symbol": "TATAMOTORS",
    "record_date": "2025-10-14",
    "quantity_ratio": 1.0,
    "source_url": (
        "https://nsearchives.nseindia.com/corporate/"
        "TATAMOTORSSJS_12112025224654_NSEBSECOAFINAL.pdf"
    ),
    "successors": (
        {
            "symbol": "TMPV",
            "company": "Tata Motors Passenger Vehicles Limited",
            "cost_ratio": 0.6885,
        },
        {
            "symbol": "TMCV",
            "company": "Tata Motors Limited (Commercial Vehicles)",
            "cost_ratio": 0.3115,
        },
    ),
}


def _positive_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise CorporateActionError(f"{label} must be a number.") from error
    if number <= 0:
        raise CorporateActionError(f"{label} must be greater than zero.")
    return number


def resolve_tata_motors_demerger(holdings, held_on_record_date=False):
    """Replace legacy TATAMOTORS positions with the two post-demerger holdings.

    The temporary current prices preserve the legacy position's total current
    value until the market-data service replaces them with independent quotes.
    """
    if not isinstance(holdings, list) or not holdings:
        raise CorporateActionError("A non-empty holdings list is required.")
    if held_on_record_date is not True:
        raise CorporateActionError(
            "Confirm that the TATAMOTORS shares were held on the 14 October 2025 "
            "record date before applying the 1:1 demerger entitlement."
        )

    resolved = []
    legacy_count = 0
    for holding in holdings:
        symbol = str(holding.get("symbol") or "").strip().upper()
        if symbol != TATA_MOTORS_DEMERGER["legacy_symbol"]:
            resolved.append(deepcopy(holding))
            continue

        legacy_count += 1
        quantity = _positive_number(holding.get("quantity"), "TATAMOTORS quantity")
        average_price = _positive_number(
            holding.get("average_price"),
            "TATAMOTORS average price",
        )
        current_price = _positive_number(
            holding.get("current_price"),
            "TATAMOTORS current price",
        )

        for successor in TATA_MOTORS_DEMERGER["successors"]:
            cost_ratio = successor["cost_ratio"]
            updated = deepcopy(holding)
            updated.update(
                {
                    "symbol": successor["symbol"],
                    "company": successor["company"],
                    "quantity": quantity * TATA_MOTORS_DEMERGER["quantity_ratio"],
                    "average_price": round(average_price * cost_ratio, 4),
                    "current_price": round(current_price * cost_ratio, 4),
                    "sector": "Automobile",
                    "market_cap": holding.get("market_cap") or "Large Cap",
                    "price_source": "Temporary demerger allocation",
                    "corporate_action_source_symbol": "TATAMOTORS",
                }
            )
            resolved.append(updated)

    if legacy_count == 0:
        raise CorporateActionError("No legacy TATAMOTORS holding was found to resolve.")

    resolution = {
        "action": "tata_motors_demerger",
        "status": "resolved",
        "legacy_symbol": "TATAMOTORS",
        "record_date": TATA_MOTORS_DEMERGER["record_date"],
        "quantity_entitlement": "1 TMPV share retained and 1 TMCV share allotted for each legacy share",
        "cost_allocation": {"TMPV": 68.85, "TMCV": 31.15},
        "resolved_positions": legacy_count,
        "source_url": TATA_MOTORS_DEMERGER["source_url"],
    }
    return resolved, resolution
