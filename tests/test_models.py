import pytest
from pydantic import ValidationError

from app.graph.models import ResearchSummary, InvestmentDecision, Recommendation, InvestmentHorizon


def test_research_summary_model():
    research = ResearchSummary(
        summary="Strong business fundamentals.",
        key_factors=[
            "Revenue growth",
            "Profitability",
            "Competitive position",
        ],
    )

    assert research.summary == "Strong business fundamentals."

    assert research.key_factors == [
        "Revenue growth",
        "Profitability",
        "Competitive position",
    ]



def test_recommendation_accepts_valid_values():
    decision = InvestmentDecision(
        recommendation=Recommendation.BUY,
        investment_horizon=InvestmentHorizon.LONG_TERM,
        investment_thesis="Strong long-term business fundamentals.",
    )

    assert decision.recommendation == Recommendation.BUY
    assert decision.investment_horizon == InvestmentHorizon.LONG_TERM


def test_recommendation_rejects_invalid_value():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            recommendation="Maybe Buy",
            investment_horizon=InvestmentHorizon.LONG_TERM,
            investment_thesis="Test thesis.",
        )


def test_investment_horizon_rejects_invalid_value():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            recommendation=Recommendation.HOLD,
            investment_horizon="Forever",
            investment_thesis="Test thesis.",
        )


def test_all_recommendation_values_are_defined():
    assert {item.value for item in Recommendation} == {
        "Strong Buy",
        "Buy",
        "Hold",
        "Reduce",
        "Sell",
    }


def test_all_investment_horizon_values_are_defined():
    assert {item.value for item in InvestmentHorizon} == {
        "Short Term",
        "Medium Term",
        "Long Term",
    }