from pydantic import BaseModel, Field
from langchain_core.tools import tool

from app.providers.exceptions import TransientProviderError
from app.providers.financial import MockStockPriceProvider, MockCompanyInfoProvider

stock_price_provider = MockStockPriceProvider()
company_info_provider = MockCompanyInfoProvider()

class TransientToolError(Exception):
    """Temporary tool failure that may succeed when retried."""


class StockPriceInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a stock ticker."""

    try:
        return stock_price_provider.get_stock_price(ticker)

    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc


class CompanyInfoInput(BaseModel):
    ticker: str = Field(
        description="Stock ticker symbol, for example AAPL or MSFT."
    )


@tool(args_schema=CompanyInfoInput)
def get_company_info(ticker: str) -> dict:
    """Get basic company information for a stock ticker."""

    try:
        return company_info_provider.get_company_info(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc