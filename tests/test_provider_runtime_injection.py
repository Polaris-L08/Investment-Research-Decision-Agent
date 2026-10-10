from dataclasses import replace

from app.providers.config import ProviderSettings
from app.providers.factory import create_provider_bundle
from app.providers.runtime import configure_provider_bundle, get_provider_bundle
from app.tools.financial import get_stock_price


def test_tool_uses_injected_runtime_provider():
    class FixedStockPriceProvider:
        def get_stock_price(self, ticker: str) -> dict:
            return {"ticker": ticker, "price": 123.45, "source": "test-double"}

    original_bundle = get_provider_bundle()
    injected_bundle = create_provider_bundle(
        ProviderSettings(app_env="test", mode="mock")
    )
    injected_bundle = replace(
        injected_bundle,
        stock_price=FixedStockPriceProvider(),
    )
    try:
        configure_provider_bundle(injected_bundle)
        result = get_stock_price.invoke({"ticker": "TEST"})
        assert result == {
            "ticker": "TEST",
            "price": 123.45,
            "source": "test-double",
        }
    finally:
        configure_provider_bundle(original_bundle)
