from collections import defaultdict
from datetime import datetime, timezone

from services.report_generator import build_automated_report


REQUIRED_FIELDS = {
    "symbol",
    "quantity",
    "average_price",
    "current_price",
    "sector",
    "market_cap",
}


def _round(value, digits=2):
    return round(float(value), digits)


def _clamp(value, minimum=0, maximum=100):
    return min(maximum, max(minimum, value))


def _validate_holding(holding, index):
    missing = REQUIRED_FIELDS.difference(holding)
    if missing:
        raise KeyError(
            f"Holding {index + 1} is missing: {', '.join(sorted(missing))}."
        )

    for field in ("quantity", "average_price", "current_price"):
        value = holding[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{field} for {holding['symbol']} must be a number.")
        if value < 0:
            raise ValueError(f"{field} for {holding['symbol']} cannot be negative.")

    if holding["quantity"] == 0:
        raise ValueError(f"Quantity for {holding['symbol']} must be greater than zero.")


def _allocation(items, total_value):
    return [
        {"name": name, "value": _round(value), "percentage": _round(value / total_value * 100)}
        for name, value in sorted(items.items(), key=lambda item: item[1], reverse=True)
    ]


def _group_performance(groups, current_value):
    result = []
    for name, values in groups.items():
        invested = values["invested"]
        current = values["current"]
        pnl = current - invested
        result.append(
            {
                "name": name,
                "invested_value": _round(invested),
                "current_value": _round(current),
                "pnl": _round(pnl),
                "return_percentage": _round(pnl / invested * 100 if invested else 0),
                "weight": _round(current / current_value * 100),
            }
        )
    return sorted(result, key=lambda item: item["current_value"], reverse=True)


def _risk_level(score):
    if score < 35:
        return "Low"
    if score < 65:
        return "Moderate"
    return "High"


def _stress_scenario(name, description, affected_value, shock, current_value):
    impact = affected_value * shock / 100
    return {
        "name": name,
        "description": description,
        "shock_percentage": shock,
        "affected_value": _round(affected_value),
        "estimated_change": _round(impact),
        "portfolio_impact_percentage": _round(impact / current_value * 100),
        "stressed_value": _round(current_value + impact),
    }


def analyse_portfolio(
    holdings,
    portfolio_name="Demo Indian Equity Portfolio",
    data_notice="Demonstration prices only — not live market data.",
):
    if not holdings:
        raise ValueError("Portfolio must contain at least one holding.")

    for index, holding in enumerate(holdings):
        _validate_holding(holding, index)

    invested_value = sum(item["quantity"] * item["average_price"] for item in holdings)
    current_value = sum(item["quantity"] * item["current_price"] for item in holdings)

    if current_value <= 0:
        raise ValueError("Current portfolio value must be greater than zero.")

    total_pnl = current_value - invested_value
    total_return = total_pnl / invested_value * 100 if invested_value else 0
    sector_values = defaultdict(float)
    market_cap_values = defaultdict(float)
    sector_groups = defaultdict(lambda: {"invested": 0.0, "current": 0.0})
    market_cap_groups = defaultdict(lambda: {"invested": 0.0, "current": 0.0})
    analysed_holdings = []

    for item in holdings:
        invested = item["quantity"] * item["average_price"]
        current = item["quantity"] * item["current_price"]
        pnl = current - invested
        return_percentage = pnl / invested * 100 if invested else 0
        weight = current / current_value * 100
        break_even_move = (item["average_price"] - item["current_price"]) / item["current_price"] * 100 if item["current_price"] else 0

        sector_values[item["sector"]] += current
        market_cap_values[item["market_cap"]] += current
        sector_groups[item["sector"]]["invested"] += invested
        sector_groups[item["sector"]]["current"] += current
        market_cap_groups[item["market_cap"]]["invested"] += invested
        market_cap_groups[item["market_cap"]]["current"] += current
        analysed_holdings.append(
            {
                **item,
                "invested_value": _round(invested),
                "current_value": _round(current),
                "pnl": _round(pnl),
                "return_percentage": _round(return_percentage),
                "weight": _round(weight),
                "return_contribution": _round(pnl / invested_value * 100 if invested_value else 0),
                "move_to_break_even": _round(break_even_move),
            }
        )

    analysed_holdings.sort(key=lambda item: item["current_value"], reverse=True)
    equal_weight = 100 / len(analysed_holdings)
    for item in analysed_holdings:
        item["equal_weight_gap"] = _round(item["weight"] - equal_weight)

    sector_allocation = _allocation(sector_values, current_value)
    market_cap_allocation = _allocation(market_cap_values, current_value)
    sector_performance = _group_performance(sector_groups, current_value)
    market_cap_performance = _group_performance(market_cap_groups, current_value)

    largest_weight = analysed_holdings[0]["weight"]
    top_three_weight = sum(item["weight"] for item in analysed_holdings[:3])
    hhi = sum((item["weight"] / 100) ** 2 for item in analysed_holdings)
    effective_holdings = 1 / hhi if hhi else 0
    largest_sector = sector_allocation[0]
    mid_small_value = sum(
        item["value"]
        for item in market_cap_allocation
        if item["name"] in {"Mid Cap", "Small Cap"}
    )
    mid_small_weight = mid_small_value / current_value * 100

    stock_risk = _clamp(largest_weight * 2.5)
    sector_risk = _clamp(largest_sector["percentage"] * 2)
    size_risk = _clamp(mid_small_weight)
    breadth_risk = _clamp((8 - min(len(holdings), 8)) / 8 * 100)
    risk_score = _round(
        stock_risk * 0.35
        + sector_risk * 0.30
        + size_risk * 0.15
        + breadth_risk * 0.20
    )

    concentration_penalty = min(40, max(0, largest_weight - 12) * 1.3 + max(0, top_three_weight - 45) * 0.55)
    sector_penalty = min(30, max(0, largest_sector["percentage"] - 22) * 0.9)
    breadth_penalty = max(0, 10 - len(holdings)) * 2.5
    diversification_score = _round(_clamp(100 - concentration_penalty - sector_penalty - breadth_penalty))

    gross_gains = sum(max(item["pnl"], 0) for item in analysed_holdings)
    gross_losses = abs(sum(min(item["pnl"], 0) for item in analysed_holdings))
    winners = [item for item in analysed_holdings if item["pnl"] > 0]
    losers = [item for item in analysed_holdings if item["pnl"] < 0]
    flat = [item for item in analysed_holdings if item["pnl"] == 0]
    profitable_weight = sum(item["weight"] for item in winners)
    loss_making_weight = sum(item["weight"] for item in losers)
    best_holding = max(analysed_holdings, key=lambda item: item["return_percentage"])
    worst_holding = min(analysed_holdings, key=lambda item: item["return_percentage"])
    performance_score = _clamp(50 + total_return * 2)
    health_score = _round(
        diversification_score * 0.40
        + (100 - risk_score) * 0.30
        + performance_score * 0.20
        + profitable_weight * 0.10
    )

    if largest_weight >= 25 or top_three_weight >= 70:
        concentration_level = "High"
    elif largest_weight >= 15 or top_three_weight >= 50:
        concentration_level = "Moderate"
    else:
        concentration_level = "Low"

    risk_breakdown = [
        {
            "name": "Single-stock concentration",
            "score": _round(stock_risk),
            "level": _risk_level(stock_risk),
            "detail": f"Largest holding is {largest_weight:.1f}%.",
        },
        {
            "name": "Sector concentration",
            "score": _round(sector_risk),
            "level": _risk_level(sector_risk),
            "detail": f"{largest_sector['name']} is {largest_sector['percentage']:.1f}%.",
        },
        {
            "name": "Mid/small-cap exposure",
            "score": _round(size_risk),
            "level": _risk_level(size_risk),
            "detail": f"Mid and small caps form {mid_small_weight:.1f}%.",
        },
        {
            "name": "Limited breadth",
            "score": _round(breadth_risk),
            "level": _risk_level(breadth_risk),
            "detail": f"Portfolio contains {len(holdings)} holdings.",
        },
    ]

    stress_scenarios = [
        _stress_scenario(
            "Broad market correction",
            "Every holding declines by 10%.",
            current_value,
            -10,
            current_value,
        ),
        _stress_scenario(
            f"{largest_sector['name']} sector shock",
            f"The largest sector declines by 15%.",
            largest_sector["value"],
            -15,
            current_value,
        ),
        _stress_scenario(
            "Mid/small-cap selloff",
            "Mid and small-cap holdings decline by 20%.",
            mid_small_value,
            -20,
            current_value,
        ),
        _stress_scenario(
            f"{analysed_holdings[0]['symbol']} drawdown",
            "The largest holding declines by 25%.",
            analysed_holdings[0]["current_value"],
            -25,
            current_value,
        ),
    ]

    insights = []
    if largest_weight >= 25:
        insights.append(
            {
                "type": "warning",
                "title": "Single-stock concentration",
                "message": f"{analysed_holdings[0]['symbol']} forms {largest_weight:.1f}% of the portfolio.",
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Controlled stock exposure",
                "message": f"The largest holding is {analysed_holdings[0]['symbol']} at {largest_weight:.1f}%.",
            }
        )

    if largest_sector["percentage"] >= 35:
        insights.append(
            {
                "type": "warning",
                "title": "Sector dependence",
                "message": f"{largest_sector['name']} contributes {largest_sector['percentage']:.1f}% of current value.",
            }
        )
    else:
        insights.append(
            {
                "type": "positive",
                "title": "Sector spread",
                "message": f"{largest_sector['name']} is the largest sector at {largest_sector['percentage']:.1f}%.",
            }
        )

    if losers:
        loss_drag = abs(sum(item["return_contribution"] for item in losers))
        symbols = ", ".join(item["symbol"] for item in sorted(losers, key=lambda item: item["pnl"])[:3])
        insights.append(
            {
                "type": "neutral",
                "title": "Return drag",
                "message": f"{symbols} reduce total return by approximately {loss_drag:.1f} percentage points.",
            }
        )

    if winners:
        gain_driver = max(winners, key=lambda item: item["pnl"])
        insights.append(
            {
                "type": "positive",
                "title": "Largest return driver",
                "message": f"{gain_driver['symbol']} contributes {gain_driver['return_contribution']:.1f} percentage points to portfolio return.",
            }
        )

    if len(holdings) < 6:
        insights.append(
            {
                "type": "warning",
                "title": "Limited portfolio breadth",
                "message": f"Only {len(holdings)} holdings means each position can have a larger effect on total results.",
            }
        )

    if mid_small_weight >= 40:
        insights.append(
            {
                "type": "neutral",
                "title": "Higher-volatility size mix",
                "message": f"Mid and small caps form {mid_small_weight:.1f}% of the portfolio.",
            }
        )

    result = {
        "meta": {
            "portfolio_name": portfolio_name,
            "currency": "INR",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_notice": data_notice,
        },
        "summary": {
            "invested_value": _round(invested_value),
            "current_value": _round(current_value),
            "total_pnl": _round(total_pnl),
            "total_return": _round(total_return),
            "holdings_count": len(holdings),
            "sectors_count": len(sector_values),
            "risk_score": risk_score,
            "diversification_score": diversification_score,
            "health_score": health_score,
            "largest_holding_weight": _round(largest_weight),
            "top_three_weight": _round(top_three_weight),
            "concentration_index": _round(hhi, 3),
            "effective_holdings": _round(effective_holdings, 1),
            "winners_count": len(winners),
            "losers_count": len(losers),
            "flat_count": len(flat),
        },
        "performance": {
            "gross_gains": _round(gross_gains),
            "gross_losses": _round(gross_losses),
            "profit_factor": _round(gross_gains / gross_losses) if gross_losses else None,
            "profitable_weight": _round(profitable_weight),
            "loss_making_weight": _round(loss_making_weight),
            "best_holding": {
                "symbol": best_holding["symbol"],
                "return_percentage": best_holding["return_percentage"],
                "pnl": best_holding["pnl"],
            },
            "worst_holding": {
                "symbol": worst_holding["symbol"],
                "return_percentage": worst_holding["return_percentage"],
                "pnl": worst_holding["pnl"],
            },
        },
        "concentration": {
            "level": concentration_level,
            "largest_holding": analysed_holdings[0]["symbol"],
            "largest_holding_weight": _round(largest_weight),
            "top_three_weight": _round(top_three_weight),
            "largest_sector": largest_sector["name"],
            "largest_sector_weight": largest_sector["percentage"],
            "effective_holdings": _round(effective_holdings, 1),
            "equal_weight_reference": _round(equal_weight),
        },
        "holdings": analysed_holdings,
        "sector_allocation": sector_allocation,
        "market_cap_allocation": market_cap_allocation,
        "sector_performance": sector_performance,
        "market_cap_performance": market_cap_performance,
        "risk_breakdown": risk_breakdown,
        "stress_scenarios": stress_scenarios,
        "insights": insights,
    }
    result["automated_report"] = build_automated_report(result)
    return result
