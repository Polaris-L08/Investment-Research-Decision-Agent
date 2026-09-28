import pytest

from app.providers.financial import (
    MockIndustryInfoProvider,
    MockMacroEnvironmentProvider,
)


def test_industry_info_provider_returns_mock_data():
    provider = MockIndustryInfoProvider()

    result = provider.get_industry_info("AAPL")

    assert result["industry"] == "Consumer Electronics"
    assert result["industry_growth"] == 6.2


def test_industry_info_provider_rejects_unknown_ticker():
    provider = MockIndustryInfoProvider()

    with pytest.raises(ValueError):
        provider.get_industry_info("UNKNOWN")


def test_macro_environment_provider_returns_mock_data():
    provider = MockMacroEnvironmentProvider()

    result = provider.get_macro_environment("AAPL")

    assert result["macro_environment"] == "Expansion"
    assert result["macro_growth"] == 2.8


def test_macro_environment_provider_rejects_unknown_ticker():
    provider = MockMacroEnvironmentProvider()

    with pytest.raises(ValueError):
        provider.get_macro_environment("UNKNOWN")