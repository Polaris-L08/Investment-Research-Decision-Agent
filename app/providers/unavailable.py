"""Fail-closed placeholders for real capabilities without a configured adapter."""

from app.providers.config import ProviderConfigurationError


class UnavailableRealProvider:
    """Preserves the provider surface without silently substituting mock data."""

    def __init__(self, capability: str) -> None:
        self._capability = capability

    def _raise(self):
        raise ProviderConfigurationError(
            f"No real provider adapter is configured for capability {self._capability!r}. "
            "No Mock fallback was used."
        )

    def get_company_info(self, ticker: str):
        self._raise()

    def get_revenue(self, ticker: str):
        self._raise()

    def get_net_income(self, ticker: str):
        self._raise()

    def get_market_index(self, ticker: str):
        self._raise()

    def get_market_return(self, ticker: str):
        self._raise()

    def get_industry_info(self, ticker: str):
        self._raise()

    def get_macro_environment(self, ticker: str):
        self._raise()

    def get_valuation_inputs(self, ticker: str):
        self._raise()

    def get_valuation_assumptions(self, ticker: str):
        self._raise()
