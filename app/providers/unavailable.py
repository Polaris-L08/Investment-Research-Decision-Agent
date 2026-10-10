"""Fail-closed placeholders for real providers not implemented yet in M7."""

from app.providers.config import ProviderConfigurationError


class UnavailableRealProvider:
    """Preserves the provider surface without silently substituting mock data."""

    def __init__(self, capability: str) -> None:
        self._capability = capability

    def _raise(self):
        raise ProviderConfigurationError(
            f"Real provider capability {self._capability!r} is not implemented yet. "
            "No Mock fallback was used; implement its real adapter in a later M7 lesson."
        )

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
