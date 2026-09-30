import pytest
from pydantic import ValidationError

from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)


def make_valid_decision() -> InvestmentDecision:
    return InvestmentDecision(
        ticker="NVDA",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=216.0,
        expected_upside=0.20,
        conviction=InvestmentConviction.HIGH,
        investment_thesis=(
            "The investment thesis is supported by strong growth "
            "prospects and favorable industry demand."
        ),
        key_catalysts=[
            "Continued AI infrastructure investment",
            "Strong demand for accelerated computing",
        ],
        key_risks=[
            "Competitive pressure",
            "Valuation multiple compression",
        ],
        invalidation_conditions=[
            "Material deterioration in growth expectations",
            "Sustained loss of competitive position",
        ],
        supporting_evidence=[
            "Strong financial growth",
            "Positive industry outlook",
            "Valuation analysis",
        ],
    )


def test_investment_decision_accepts_valid_model():
    decision = make_valid_decision()

    assert decision.ticker == "NVDA"
    assert decision.recommendation == InvestmentRecommendation.BUY
    assert decision.investment_horizon == InvestmentHorizon.MEDIUM_TERM
    assert decision.conviction == InvestmentConviction.HIGH
    assert decision.current_price == 180.0
    assert decision.target_price == 216.0
    assert decision.expected_upside == 0.20


def test_investment_recommendation_enum_values():
    assert InvestmentRecommendation.STRONG_BUY.value == "Strong Buy"
    assert InvestmentRecommendation.BUY.value == "Buy"
    assert InvestmentRecommendation.HOLD.value == "Hold"
    assert InvestmentRecommendation.REDUCE.value == "Reduce"
    assert InvestmentRecommendation.SELL.value == "Sell"


def test_investment_horizon_enum_values():
    assert InvestmentHorizon.SHORT_TERM.value == "Short Term"
    assert InvestmentHorizon.MEDIUM_TERM.value == "Medium Term"
    assert InvestmentHorizon.LONG_TERM.value == "Long Term"


def test_investment_conviction_enum_values():
    assert InvestmentConviction.LOW.value == "Low"
    assert InvestmentConviction.MEDIUM.value == "Medium"
    assert InvestmentConviction.HIGH.value == "High"


def test_expected_upside_must_match_prices():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.50,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_negative_target_price_is_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=-1.0,
            expected_upside=-1.0055555556,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_zero_current_price_is_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=0.0,
            target_price=180.0,
            expected_upside=1.0,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_empty_ticker_is_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.20,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_empty_investment_thesis_is_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.20,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_empty_key_risks_are_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.20,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=[],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
        )


def test_empty_supporting_evidence_is_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.20,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=[],
        )


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        InvestmentDecision(
            ticker="NVDA",
            recommendation=InvestmentRecommendation.BUY,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            current_price=180.0,
            target_price=216.0,
            expected_upside=0.20,
            conviction=InvestmentConviction.HIGH,
            investment_thesis="Valid investment thesis.",
            key_catalysts=["Catalyst"],
            key_risks=["Risk"],
            invalidation_conditions=["Invalidation condition"],
            supporting_evidence=["Evidence"],
            unexpected_field="not allowed",
        )