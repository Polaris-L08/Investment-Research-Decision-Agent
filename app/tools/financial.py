from pydantic import BaseModel, Field
from langchain_core.tools import tool


class TransientToolError(Exception):
    """Temporary tool failure that may succeed when retried."""


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    if ticker == "TEMP_ERROR":
        raise TransientToolError(
            "Temporary stock price provider error."
        )

    mock_prices = {
        "AAPL": 200.0,
        "MSFT": 450.0,
        "GOOGL": 180.0,
    }

    if ticker not in mock_prices:
        raise ValueError(
            f"Stock price not found for ticker: {ticker}"
        )

    return {
        "ticker": ticker,
        "price": mock_prices[ticker],
    }