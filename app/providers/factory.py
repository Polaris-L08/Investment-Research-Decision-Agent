"""Central construction point for the application's data providers."""
import os
from dataclasses import dataclass

from app.providers.alpha_vantage import AlphaVantageClient, AlphaVantageStockPriceProvider, \
    AlphaVantageCompanyInfoProvider, AlphaVantageIncomeStatementProvider
from app.providers.config import ProviderConfigurationError, ProviderSettings
from app.providers.financial import (
    CompanyInfoProvider,
    IndustryInfoProvider,
    MacroEnvironmentProvider,
    MarketIndexProvider,
    MarketReturnProvider,
    MockCompanyInfoProvider,
    MockIndustryInfoProvider,
    MockMacroEnvironmentProvider,
    MockMarketIndexProvider,
    MockMarketReturnProvider,
    MockNetIncomeInfoProvider,
    MockRevenueInfoProvider,
    MockStockPriceProvider,
    MockValuationResearchProvider,
    NetIncomeInfoProvider,
    RevenueInfoProvider,
    StockPriceProvider,
    ValuationResearchProvider,
)
from app.providers.unavailable import UnavailableRealProvider


@dataclass(frozen=True)
class ProviderBundle:
    """All provider dependencies required by the current application graph."""

    stock_price: StockPriceProvider
    company_info: CompanyInfoProvider
    revenue: RevenueInfoProvider
    net_income: NetIncomeInfoProvider
    market_index: MarketIndexProvider
    market_return: MarketReturnProvider
    industry_info: IndustryInfoProvider
    macro_environment: MacroEnvironmentProvider
    valuation_research: ValuationResearchProvider
    mode: str


def create_provider_bundle(
    settings: ProviderSettings | None = None,
) -> ProviderBundle:
    """Build providers from explicit runtime settings.

    Real mode currently supports quote, company-profile, annual revenue, and net-income adapters.
    Other capabilities fail closed until their adapters are implemented; this
    factory never silently mixes Mock data into a real-mode bundle.
    """
    resolved = settings or ProviderSettings.from_env()

    if resolved.mode == "real":
        if resolved.app_env == "production":
            raise ProviderConfigurationError(
                "Real provider coverage is incomplete: only stock quotes and "
                "company profiles, revenue, and net income are implemented in M7 Lessons 3-4. Production "
                "mode remains blocked until all required real providers and "
                "operational controls are implemented."
            )

        client = AlphaVantageClient(api_key=os.getenv("ALPHA_VANTAGE_API_KEY"))
        income_statement = AlphaVantageIncomeStatementProvider(client)
        unavailable = UnavailableRealProvider("market benchmark/industry/macro/valuation research")
        return ProviderBundle(
            stock_price=AlphaVantageStockPriceProvider(client),
            company_info=AlphaVantageCompanyInfoProvider(client),
            revenue=income_statement,
            net_income=income_statement,
            market_index=unavailable,
            market_return=unavailable,
            industry_info=unavailable,
            macro_environment=unavailable,
            valuation_research=unavailable,
            mode="real-partial",
        )

    if resolved.mode != "mock":
        raise ProviderConfigurationError(
            f"Unsupported provider mode: {resolved.mode!r}."
        )

    return ProviderBundle(
        stock_price=MockStockPriceProvider(),
        company_info=MockCompanyInfoProvider(),
        revenue=MockRevenueInfoProvider(),
        net_income=MockNetIncomeInfoProvider(),
        market_index=MockMarketIndexProvider(),
        market_return=MockMarketReturnProvider(),
        industry_info=MockIndustryInfoProvider(),
        macro_environment=MockMacroEnvironmentProvider(),
        valuation_research=MockValuationResearchProvider(),
        mode="mock",
    )
