from app.providers.financial import (
    MockCompanyInfoProvider,
    MockStockPriceProvider,
)


def test_mock_stock_price_provider():
    provider = MockStockPriceProvider()

    result = provider.get_stock_price("AAPL")

    assert result == {
        "ticker": "AAPL",
        "price": 200.0,
    }


def test_mock_company_info_provider():
    provider = MockCompanyInfoProvider()

    result = provider.get_company_info("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["sector"] == "Technology"