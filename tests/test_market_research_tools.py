from app.tools.financial import (
    get_market_index,
    get_market_return,
)


def test_get_market_index_tool():
    result = get_market_index.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result == "S&P 500"


def test_get_market_return_tool():
    result = get_market_return.invoke(
        {
            "ticker": "AAPL",
        }
    )

    assert result == 8.5