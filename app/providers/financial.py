from abc import ABC, abstractmethod

from app.providers.exceptions import TransientProviderError


class StockPriceProvider(ABC):

    @abstractmethod
    def get_stock_price(self, ticker: str) -> dict:
        raise NotImplementedError


class MockStockPriceProvider(StockPriceProvider):

    def __init__(self):
        self.mock_prices = {
            "AAPL": 200.0,
            "MSFT": 450.0,
            "GOOGL": 180.0,
        }

    def get_stock_price(self, ticker: str) -> dict:
        if ticker == "TEMP_ERROR":
            raise TransientProviderError(
                "Temporary stock price provider error."
            )

        if ticker not in self.mock_prices:
            raise ValueError(
                f"Stock price not found for ticker: {ticker}"
            )

        return {
            "ticker": ticker,
            "price": self.mock_prices[ticker],
        }


class CompanyInfoProvider(ABC):

    @abstractmethod
    def get_company_info(self, ticker: str) -> dict:
        raise NotImplementedError


class MockCompanyInfoProvider(CompanyInfoProvider):

    def __init__(self):
        self.mock_companies = {
            "AAPL": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
            },
            "MSFT": {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation",
                "sector": "Technology",
            },
            "GOOGL": {
                "ticker": "GOOGL",
                "company_name": "Alphabet Inc.",
                "sector": "Communication Services",
            },
        }

    def get_company_info(self, ticker: str) -> dict:
        if ticker not in self.mock_companies:
            raise ValueError(
                f"Company information not found for ticker: {ticker}"
            )

        return self.mock_companies[ticker]