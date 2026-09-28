from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.providers.exceptions import TransientProviderError
from app.providers.financial import MockStockPriceProvider, MockCompanyInfoProvider, MockRevenueInfoProvider, \
    MockNetIncomeInfoProvider, MockMarketIndexProvider, MockMarketReturnProvider

stock_price_provider = MockStockPriceProvider()
company_info_provider = MockCompanyInfoProvider()
revenue_info_provider = MockRevenueInfoProvider()
net_income_info_provider = MockNetIncomeInfoProvider()
market_index_provider = MockMarketIndexProvider()
market_return_provider = MockMarketReturnProvider()

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

class RevenueInput(BaseModel):
    ticker: str = Field(
        description="Company revenue symbol, for example AAPL or MSFT."
    )

@tool(args_schema=RevenueInput)
def get_revenue(ticker: str) -> float:
    """Get company revenue for the given stock ticker."""
    try:
        return revenue_info_provider.get_revenue(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc


class NetIncomeInput(BaseModel):
    ticker: str = Field(
        description="Company net incoming for the given stock ticker."
    )

@tool(args_schema=NetIncomeInput)
def get_net_income(ticker: str) -> float:
    """Get company net income for the given stock ticker."""
    try:
        return net_income_info_provider.get_net_income(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc


class MarketIndexInput(BaseModel):
    ticker: str = Field()

@tool(args_schema=MarketIndexInput)
def get_market_index(ticker: str) -> str:
    """Get company market index for the given stock ticker."""
    try:
        return market_index_provider.get_market_index(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc


class MarketReturnInput(BaseModel):
    ticker: str = Field()

@tool(args_schema=MarketReturnInput)
def get_market_return(ticker: str) -> float:
    """Get company market return for the given stock ticker."""
    try:
        return market_return_provider.get_market_return(ticker)
    except TransientProviderError as exc:
        raise TransientToolError(
            str(exc)
        ) from exc