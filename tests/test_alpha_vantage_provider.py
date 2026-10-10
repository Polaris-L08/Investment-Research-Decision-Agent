import json

import pytest

from app.providers.alpha_vantage import (
    AlphaVantageClient,
    AlphaVantageCompanyInfoProvider,
    AlphaVantageStockPriceProvider,
)
from app.providers.config import ProviderConfigurationError
from app.providers.exceptions import TransientProviderError


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


def provider_for(payload):
    client = AlphaVantageClient(
        api_key="test-key",
        opener=lambda request, timeout: FakeResponse(payload),
    )
    return client


def test_stock_price_provider_normalizes_alpha_vantage_quote():
    provider = AlphaVantageStockPriceProvider(
        provider_for(
            {
                "Global Quote": {
                    "01. symbol": "AAPL",
                    "05. price": "231.4500",
                    "07. latest trading day": "2026-10-09",
                }
            }
        )
    )

    result = provider.get_stock_price(" aapl ")

    assert result == {
        "ticker": "AAPL",
        "price": 231.45,
        "latest_trading_day": "2026-10-09",
        "source": "Alpha Vantage GLOBAL_QUOTE",
    }


def test_company_info_provider_normalizes_overview():
    provider = AlphaVantageCompanyInfoProvider(
        provider_for(
            {
                "Symbol": "MSFT",
                "Name": "Microsoft Corporation",
                "Sector": "Technology",
                "Industry": "Software - Infrastructure",
                "Exchange": "NASDAQ",
                "Currency": "USD",
                "MarketCapitalization": "3500000000000",
                "Description": "A software company.",
            }
        )
    )

    result = provider.get_company_info("msft")

    assert result["ticker"] == "MSFT"
    assert result["company_name"] == "Microsoft Corporation"
    assert result["sector"] == "Technology"
    assert result["market_cap"] == 3500000000000.0
    assert result["source"] == "Alpha Vantage OVERVIEW"


def test_missing_api_key_fails_fast(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    with pytest.raises(ProviderConfigurationError, match="ALPHA_VANTAGE_API_KEY"):
        AlphaVantageClient()


def test_api_rate_limit_notice_is_transient():
    client = provider_for({"Note": "API call frequency is exceeded."})
    with pytest.raises(TransientProviderError, match="limit/availability notice"):
        client.get_json("GLOBAL_QUOTE", "AAPL")


def test_api_entitlement_notice_is_not_misclassified_as_transient():
    client = provider_for({"Information": "This endpoint requires a premium subscription."})
    with pytest.raises(ProviderConfigurationError, match="entitlement notice"):
        client.get_json("GLOBAL_QUOTE", "AAPL")


def test_empty_quote_response_is_not_reported_as_a_valid_quote():
    provider = AlphaVantageStockPriceProvider(provider_for({}))
    with pytest.raises(ValueError, match="No quote data"):
        provider.get_stock_price("AAPL")


def test_invalid_price_is_transient_provider_error():
    provider = AlphaVantageStockPriceProvider(
        provider_for({"Global Quote": {"01. symbol": "AAPL", "05. price": "N/A"}})
    )
    with pytest.raises(TransientProviderError, match="invalid price"):
        provider.get_stock_price("AAPL")
