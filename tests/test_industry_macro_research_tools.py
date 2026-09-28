from app.tools.financial import (
    get_industry_info,
    get_macro_environment,
)


def test_get_industry_info_tool():
    result = get_industry_info.invoke(
        {"ticker": "AAPL"}
    )

    assert result["industry"] == "Consumer Electronics"
    assert result["industry_growth"] == 6.2


def test_get_macro_environment_tool():
    result = get_macro_environment.invoke(
        {"ticker": "AAPL"}
    )

    assert result["macro_environment"] == "Expansion"
    assert result["macro_growth"] == 2.8