import pytest

from app.tools.financial import get_stock_price


def test_get_stock_price():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0


def test_get_stock_price_aapl():
    result = get_stock_price.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0


def test_get_stock_price_msft():
    result = get_stock_price.invoke(
        {"ticker": "MSFT"}
    )

    assert result["ticker"] == "MSFT"
    assert result["price"] == 450.0


from app.tools.financial import (
    StockPriceInput,
    get_stock_price,
)


def test_tool_name():
    assert get_stock_price.name == "get_stock_price"


def test_tool_schema_contains_ticker():
    schema = get_stock_price.args

    assert "ticker" in schema
    assert schema["ticker"]["type"] == "string"


def test_stock_price_input_schema():
    schema = StockPriceInput.model_json_schema()

    assert "ticker" in schema["properties"]
    assert schema["properties"]["ticker"]["type"] == "string"


def test_get_stock_price_invalid_ticker():
    with pytest.raises(ValueError, match="INVALID"):
        get_stock_price.invoke(
            {"ticker": "INVALID"}
        )