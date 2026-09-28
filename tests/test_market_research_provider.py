import pytest

from app.providers.financial import (
    MockMarketIndexProvider,
    MockMarketReturnProvider,
)


def test_market_index_provider_returns_mock_index():
    provider = MockMarketIndexProvider()

    result = provider.get_market_index("AAPL")

    assert result == "S&P 500"


def test_market_index_provider_rejects_unknown_ticker():
    provider = MockMarketIndexProvider()

    with pytest.raises(ValueError):
        provider.get_market_index("UNKNOWN")


def test_market_return_provider_returns_mock_return():
    provider = MockMarketReturnProvider()

    result = provider.get_market_return("AAPL")

    assert result == 8.5


def test_market_return_provider_rejects_unknown_ticker():
    provider = MockMarketReturnProvider()

    with pytest.raises(ValueError):
        provider.get_market_return("UNKNOWN")