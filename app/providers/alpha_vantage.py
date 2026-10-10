"""Alpha Vantage adapters for quote and company-profile data.

The HTTP layer uses the Python standard library so this adapter does not add a
runtime dependency. Keep the API key outside source control.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError
from app.providers.financial import CompanyInfoProvider, StockPriceProvider


class AlphaVantageClient:
    """Small, testable HTTP client for Alpha Vantage's JSON API."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 10.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.getenv("ALPHA_VANTAGE_API_KEY")
        if not resolved_key or not resolved_key.strip():
            raise ProviderConfigurationError(
                "ALPHA_VANTAGE_API_KEY is required when PROVIDER_MODE=real."
            )
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")
        self._api_key = resolved_key.strip()
        self._timeout = timeout
        self._opener = opener or urlopen

    def get_json(self, function: str, symbol: str) -> dict[str, Any]:
        params = urlencode(
            {
                "function": function,
                "symbol": symbol,
                "apikey": self._api_key,
            }
        )
        request = Request(
            f"{self.BASE_URL}?{params}",
            headers={"User-Agent": "Investment-Research-Decision-Agent/1.0"},
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                status = getattr(response, "status", 200)
                if status >= 500:
                    raise TransientProviderError(
                        f"Alpha Vantage returned HTTP {status}."
                    )
                raw_body = response.read()
        except HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise TransientProviderError(
                    f"Alpha Vantage returned temporary HTTP error {exc.code}."
                ) from exc
            raise ValueError(
                f"Alpha Vantage request failed with HTTP {exc.code}."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise TransientProviderError(
                f"Unable to reach Alpha Vantage: {exc}"
            ) from exc

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransientProviderError(
                "Alpha Vantage returned a response that was not valid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise TransientProviderError(
                "Alpha Vantage returned an unexpected JSON structure."
            )

        # Alpha Vantage reports quota/rate-limit conditions in JSON on some plans.
        if "Note" in payload:
            detail = str(payload["Note"])
            raise TransientProviderError(f"Alpha Vantage limit/availability notice: {detail}")
        if "Information" in payload:
            # This field may indicate an invalid key, a premium-only endpoint,
            # or an account entitlement issue; retrying cannot reliably fix it.
            raise ProviderConfigurationError(
                f"Alpha Vantage API key/endpoint entitlement notice: {payload['Information']}"
            )
        if "Error Message" in payload:
            raise ValueError(f"Alpha Vantage rejected the request: {payload['Error Message']}")
        return payload


class AlphaVantageStockPriceProvider(StockPriceProvider):
    def __init__(self, client: AlphaVantageClient | None = None) -> None:
        self._client = client or AlphaVantageClient()

    def get_stock_price(self, ticker: str) -> dict[str, Any]:
        symbol = _normalize_ticker(ticker)
        payload = self._client.get_json("GLOBAL_QUOTE", symbol)
        quote = payload.get("Global Quote")
        if not isinstance(quote, dict) or not quote:
            raise ValueError(
                f"No quote data was returned for ticker {symbol!r}. "
                "Check the symbol and the data entitlement for this API key."
            )

        returned_symbol = str(quote.get("01. symbol") or symbol).strip().upper()
        raw_price = quote.get("05. price")
        try:
            price = float(raw_price)
        except (TypeError, ValueError) as exc:
            raise TransientProviderError(
                f"Alpha Vantage returned an invalid price for {symbol}."
            ) from exc
        if not math.isfinite(price) or price <= 0:
            raise TransientProviderError(
                f"Alpha Vantage returned a non-positive or non-finite price for {symbol}."
            )

        return {
            "ticker": returned_symbol,
            "price": price,
            "latest_trading_day": quote.get("07. latest trading day"),
            "source": "Alpha Vantage GLOBAL_QUOTE",
        }


class AlphaVantageCompanyInfoProvider(CompanyInfoProvider):
    def __init__(self, client: AlphaVantageClient | None = None) -> None:
        self._client = client or AlphaVantageClient()

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        symbol = _normalize_ticker(ticker)
        payload = self._client.get_json("OVERVIEW", symbol)
        returned_symbol = str(payload.get("Symbol") or "").strip().upper()
        company_name = str(payload.get("Name") or "").strip()
        if not returned_symbol or not company_name:
            raise ValueError(
                f"No company profile was returned for ticker {symbol!r}. "
                "Check the symbol and the data entitlement for this API key."
            )

        market_cap = _optional_float(payload.get("MarketCapitalization"))
        return {
            "ticker": returned_symbol,
            "company_name": company_name,
            "sector": _optional_text(payload.get("Sector")),
            "industry": _optional_text(payload.get("Industry")),
            "exchange": _optional_text(payload.get("Exchange")),
            "currency": _optional_text(payload.get("Currency")),
            "market_cap": market_cap,
            "description": _optional_text(payload.get("Description")),
            "source": "Alpha Vantage OVERVIEW",
        }


def _normalize_ticker(ticker: str) -> str:
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a non-empty string.")
    normalized = ticker.strip().upper()
    if any(character.isspace() for character in normalized):
        raise ValueError("ticker must not contain whitespace.")
    return normalized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: Any) -> float | None:
    if value is None or str(value).strip() in {"", "None", "-"}:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
