import pytest

from app.providers.config import ProviderConfigurationError, ProviderSettings
from app.providers.factory import create_provider_bundle


def test_development_defaults_to_mock_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("PROVIDER_MODE", raising=False)

    settings = ProviderSettings.from_env()
    bundle = create_provider_bundle(settings)

    assert settings.mode == "mock"
    assert bundle.mode == "mock"
    assert bundle.stock_price.get_stock_price("AAPL")["price"] == 200.0


def test_production_requires_explicit_provider_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PROVIDER_MODE", raising=False)

    with pytest.raises(ProviderConfigurationError, match="explicitly configured"):
        ProviderSettings.from_env()


def test_production_cannot_use_mock_providers():
    with pytest.raises(ProviderConfigurationError, match="prohibited"):
        ProviderSettings(app_env="production", mode="mock")


def test_real_mode_fails_without_silent_mock_fallback():
    settings = ProviderSettings(app_env="development", mode="real")

    with pytest.raises(ProviderConfigurationError, match="No Mock fallback"):
        create_provider_bundle(settings)


def test_real_mode_registers_real_quote_and_company_providers_without_mock_fallback(monkeypatch):
    from app.providers.alpha_vantage import (
        AlphaVantageCompanyInfoProvider,
        AlphaVantageStockPriceProvider,
    )
    from app.providers.unavailable import UnavailableRealProvider

    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")
    settings = ProviderSettings(app_env="development", mode="real")
    bundle = create_provider_bundle(settings)

    assert bundle.mode == "real-partial"
    assert isinstance(bundle.stock_price, AlphaVantageStockPriceProvider)
    assert isinstance(bundle.company_info, AlphaVantageCompanyInfoProvider)
    assert isinstance(bundle.revenue, UnavailableRealProvider)
    with pytest.raises(ProviderConfigurationError, match="No Mock fallback"):
        bundle.revenue.get_revenue("AAPL")


def test_real_mode_requires_alpha_vantage_api_key(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    settings = ProviderSettings(app_env="development", mode="real")

    with pytest.raises(ProviderConfigurationError, match="ALPHA_VANTAGE_API_KEY"):
        create_provider_bundle(settings)


def test_production_real_mode_remains_blocked_until_provider_coverage_is_complete(monkeypatch):
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")
    settings = ProviderSettings(app_env="production", mode="real")

    with pytest.raises(ProviderConfigurationError, match="coverage is incomplete"):
        create_provider_bundle(settings)

