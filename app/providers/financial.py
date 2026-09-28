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


class RevenueInfoProvider(ABC):
    @abstractmethod
    def get_revenue(self, ticker: str) -> float:
        raise NotImplementedError


class MockRevenueInfoProvider(RevenueInfoProvider):
    def __init__(self):
        self.mock_revenue = {
            "AAPL": 100000.0,
            "MSFT": 80000.0,
        }

    def get_revenue(self, ticker: str) -> float:
        if ticker not in self.mock_revenue:
            raise ValueError(
                f"Revenue not found for ticker: {ticker}"
            )
        return self.mock_revenue[ticker]


class NetIncomeInfoProvider(ABC):
    @abstractmethod
    def get_net_income(self, ticker: str) -> float:
        raise NotImplementedError


class MockNetIncomeInfoProvider(NetIncomeInfoProvider):
    def __init__(self):
        self.mock_net_income = {
            "AAPL": 25000.0,
            "MSFT": 22000.0,
        }

    def get_net_income(self, ticker: str) -> float:
        if ticker not in self.mock_net_income:
            raise ValueError(
                f"Net income not found for ticker: {ticker}"
            )
        return self.mock_net_income[ticker]


class MarketIndexProvider(ABC):
    @abstractmethod
    def get_market_index(self, ticker: str) -> str:
        raise NotImplementedError


class MockMarketIndexProvider(MarketIndexProvider):
    def __init__(self):
        self.mock_market_index = {
            "AAPL": "S&P 500",
            "MSFT": "S&P 500",
        }

    def get_market_index(self, ticker: str) -> str:
        if ticker not in self.mock_market_index:
            raise ValueError(
                f"Market index not found for ticker: {ticker}"
            )
        return self.mock_market_index[ticker]


class MarketReturnProvider(ABC):
    @abstractmethod
    def get_market_return(self, ticker: str) -> float:
        raise NotImplementedError

class MockMarketReturnProvider(MarketReturnProvider):
    def __init__(self):
        self.mock_return = {
            "AAPL": 8.5,
            "MSFT": 8.5,
        }

    def get_market_return(self, ticker: str) -> float:
        if ticker not in self.mock_return:
            raise ValueError(
                f"Market return not found for ticker: {ticker}"
            )
        return self.mock_return[ticker]