import json
import os
import re
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
MAX_SYMBOLS_PER_REFRESH = 50
DEFAULT_CACHE_TTL_SECONDS = 300

_PRICE_CACHE = {}
_CACHE_LOCK = threading.Lock()

CORPORATE_ACTION_REVIEWS = {
    "TATAMOTORS": {
        "suggested_symbols": ["TMPV", "TMCV"],
        "reason": (
            "TATAMOTORS changed after the Tata Motors demerger. Review whether this "
            "holding should be represented by TMPV, TMCV, or both, and verify each "
            "adjusted acquisition cost."
        ),
    },
}


class MarketDataError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


class SymbolReviewRequired(ValueError):
    def __init__(self, symbol, reason, suggested_symbols):
        super().__init__(reason)
        self.symbol = symbol
        self.suggested_symbols = suggested_symbols


def normalise_nse_symbol(symbol):
    cleaned = str(symbol or "").strip().upper()
    for prefix in ("NSE_EQ|", "NSE:", "NSE-"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    for suffix in (".NSE", ".NS", "-EQ"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]
            break
    if not cleaned:
        raise ValueError("A holding symbol is required.")
    if not re.fullmatch(r"[A-Z0-9&.-]+", cleaned):
        raise ValueError(f"{symbol} is not a supported NSE symbol format.")
    return cleaned


def resolve_market_symbol(symbol):
    normalised = normalise_nse_symbol(symbol)
    review = CORPORATE_ACTION_REVIEWS.get(normalised)
    if review:
        raise SymbolReviewRequired(
            normalised,
            review["reason"],
            review["suggested_symbols"],
        )
    return normalised


def yahoo_ticker(symbol):
    return f"{resolve_market_symbol(symbol)}.NS"


def _iso_from_epoch(value):
    if not value:
        return None
    return datetime.fromtimestamp(float(value), timezone.utc).isoformat()


def _latest_close(result):
    quotes = (result.get("indicators") or {}).get("quote") or []
    closes = quotes[0].get("close") if quotes else []
    for value in reversed(closes or []):
        if value is not None:
            return value
    return None


def _fetch_yahoo_quote(ticker):
    encoded_ticker = quote(ticker, safe="")
    url = (
        f"{YAHOO_CHART_URL.format(ticker=encoded_ticker)}"
        "?range=1d&interval=1m&includePrePost=false"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 PortfolioLens/1.0",
        },
    )

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            raise MarketDataError(f"No NSE market quote was found for {ticker}.", 404) from error
        if error.code == 429:
            raise MarketDataError("The market-data provider is temporarily rate limiting requests.", 503) from error
        raise MarketDataError(f"The market-data provider returned HTTP {error.code}.") from error
    except (URLError, TimeoutError) as error:
        raise MarketDataError("The market-data provider could not be reached.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MarketDataError("The market-data provider returned an unreadable response.") from error

    chart = payload.get("chart") or {}
    if chart.get("error"):
        description = chart["error"].get("description") or "Quote unavailable."
        raise MarketDataError(str(description), 404)

    results = chart.get("result") or []
    if not results:
        raise MarketDataError(f"No market quote was returned for {ticker}.", 404)

    result = results[0]
    meta = result.get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        price = _latest_close(result)
    if price is None or float(price) <= 0:
        raise MarketDataError(f"No usable market price was returned for {ticker}.", 404)

    return {
        "ticker": ticker,
        "price": round(float(price), 4),
        "currency": meta.get("currency") or "INR",
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName") or "NSE",
        "market_time": _iso_from_epoch(meta.get("regularMarketTime")),
    }


def _cache_ttl_seconds():
    try:
        return max(60, min(int(os.getenv("MARKET_PRICE_CACHE_SECONDS", "300")), 3600))
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS


def _quote_for_symbol(symbol, ttl_seconds):
    ticker = yahoo_ticker(symbol)
    current_monotonic = time.monotonic()

    with _CACHE_LOCK:
        cached = _PRICE_CACHE.get(ticker)
        if cached and current_monotonic - cached["cached_at"] < ttl_seconds:
            return {**deepcopy(cached["quote"]), "cache_hit": True}

    fetched = _fetch_yahoo_quote(ticker)
    with _CACHE_LOCK:
        _PRICE_CACHE[ticker] = {
            "cached_at": current_monotonic,
            "quote": deepcopy(fetched),
        }
    return {**fetched, "cache_hit": False}


def refresh_holdings_prices(holdings):
    if not isinstance(holdings, list) or not holdings:
        raise MarketDataError("A non-empty holdings list is required.", 400)
    if len(holdings) > MAX_SYMBOLS_PER_REFRESH:
        raise MarketDataError(
            f"A maximum of {MAX_SYMBOLS_PER_REFRESH} holdings can be refreshed at once.",
            400,
        )

    ttl_seconds = _cache_ttl_seconds()
    quotes = {}
    failures = []

    for holding in holdings:
        symbol = str(holding.get("symbol") or "").strip().upper()
        try:
            quotes[symbol] = _quote_for_symbol(symbol, ttl_seconds)
        except SymbolReviewRequired as error:
            failures.append(
                {
                    "symbol": error.symbol,
                    "reason": str(error),
                    "type": "corporate_action_review",
                    "suggested_symbols": error.suggested_symbols,
                }
            )
        except (MarketDataError, ValueError) as error:
            failures.append(
                {
                    "symbol": symbol or "Unknown",
                    "reason": str(error),
                    "type": "quote_unavailable",
                    "suggested_symbols": [],
                }
            )

    if not quotes:
        raise MarketDataError(
            "No prices could be refreshed. Your existing manual prices are unchanged. "
            "Check the NSE symbols or try again later."
        )

    refreshed_at = datetime.now(timezone.utc).isoformat()
    refreshed_holdings = []
    for holding in holdings:
        updated = deepcopy(holding)
        symbol = str(updated.get("symbol") or "").strip().upper()
        market_quote = quotes.get(symbol)
        if market_quote:
            updated["current_price"] = market_quote["price"]
            updated["price_source"] = "Yahoo Finance"
            updated["price_updated_at"] = market_quote.get("market_time") or refreshed_at
            updated["market_symbol"] = market_quote["ticker"]
        refreshed_holdings.append(updated)

    market_meta = {
        "provider": "Yahoo Finance",
        "provider_code": "yahoo_chart",
        "price_type": "latest_available_snapshot",
        "fetched_at": refreshed_at,
        "cache_ttl_seconds": ttl_seconds,
        "may_be_delayed": True,
        "refreshed_symbols": list(quotes),
        "failed_symbols": failures,
        "refreshed_count": len(quotes),
        "failed_count": len(failures),
        "cache_hits": sum(1 for item in quotes.values() if item["cache_hit"]),
    }
    return refreshed_holdings, market_meta


def clear_price_cache():
    """Clear the in-memory cache. Intended for tests and local troubleshooting."""
    with _CACHE_LOCK:
        _PRICE_CACHE.clear()
