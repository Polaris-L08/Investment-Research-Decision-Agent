import pytest
from pydantic import ValidationError

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)


@pytest.mark.parametrize(
    "model,payload",
    [
        (CompanyResearchResult, {"ticker": "AAPL", "company_name": "Apple", "sector": "Technology", "current_price": 200.0, "summary": "Facts."}),
        (FinancialResearchResult, {"ticker": "AAPL", "revenue": 100.0, "net_income": 20.0, "profit_margin": 0.2, "summary": "Facts."}),
        (MarketResearchResult, {"ticker": "AAPL", "market_index": "S&P 500", "market_return": 0.1, "summary": "Facts."}),
        (IndustryMacroResearchResult, {"ticker": "AAPL", "industry": "Technology", "industry_growth": 0.1, "macro_environment": "Stable", "macro_growth": 0.02, "summary": "Facts."}),
    ],
)
def test_all_research_results_share_status_contract(model, payload):
    result = model(**payload)
    assert result.data_status == "complete"
    assert result.degradation_reason == ""

    degraded = model(**payload, data_status="degraded", degradation_reason="Structured synthesis failed; provider evidence retained.")
    assert degraded.data_status == "degraded"
    assert degraded.degradation_reason


def test_degraded_result_requires_reason():
    with pytest.raises(ValidationError, match="requires degradation_reason"):
        CompanyResearchResult(
            ticker="AAPL", company_name="Apple", sector="Technology",
            current_price=200.0, summary="Facts.", data_status="degraded",
        )


def test_complete_result_rejects_degradation_reason():
    with pytest.raises(ValidationError, match="must not have degradation_reason"):
        MarketResearchResult(
            ticker="AAPL", market_index="S&P 500", market_return=0.1,
            summary="Facts.", degradation_reason="unavailable",
        )
