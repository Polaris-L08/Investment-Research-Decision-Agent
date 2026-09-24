from langchain_core.tools import tool
from pydantic import BaseModel, Field


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT"
    )

@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    mock_prices = {
        "AAPL": 200.0,
        "MSFT": 450.0,
        "GOOGL": 180.0,
    }

    return {
        "ticker": ticker,
        "price": mock_prices.get(ticker, 100.0),
    }