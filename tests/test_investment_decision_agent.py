from unittest.mock import MagicMock, patch

from app.agents.investment_decision import (
    InvestmentDecisionInputState,
    build_investment_decision_graph,
)
from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.investment.models import (
    InvestmentConviction,
    InvestmentDecision,
    InvestmentHorizon,
    InvestmentRecommendation,
)
from app.risk.models import (
    RiskAnalysis,
    RiskCategory,
    RiskImpact,
    RiskItem,
    RiskLikelihood,
    RiskSeverity,
)
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


def make_company_research() -> CompanyResearchResult:
    return CompanyResearchResult(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        sector="Semiconductors",
        current_price=180.0,
        summary=(
            "NVIDIA designs GPUs and accelerated computing platforms "
            "serving data center and other computing markets."
        ),
    )


def make_financial_research() -> FinancialResearchResult:
    return FinancialResearchResult(
        ticker="NVDA",
        revenue=100.0,
        net_income=30.0,
        profit_margin=0.30,
        summary=(
            "The company has strong revenue and net income "
            "with a high profit margin."
        ),
    )


def make_market_research() -> MarketResearchResult:
    return MarketResearchResult(
        ticker="NVDA",
        market_index="NASDAQ",
        market_return=0.08,
        summary=(
            "The stock has experienced positive market performance "
            "within the broader technology market."
        ),
    )


def make_industry_macro_research() -> IndustryMacroResearchResult:
    return IndustryMacroResearchResult(
        ticker="NVDA",
        industry="Semiconductors",
        industry_growth=0.15,
        macro_environment="Growth-oriented technology investment environment",
        macro_growth=0.03,
        summary=(
            "The semiconductor industry benefits from AI infrastructure "
            "investment but remains exposed to macroeconomic conditions."
        ),
    )


def make_valuation() -> ValuationResult:
    return ValuationResult(
        ticker="NVDA",
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=6.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=30.0,
            rationale="Illustrative P/E multiple assumption.",
        ),
        implied_value_per_share=180.0,
        target_price=216.0,
        current_price=180.0,
        expected_upside=0.20,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="phase6-v1",
        ),
    )


def make_risk_analysis() -> RiskAnalysis:
    return RiskAnalysis(
        ticker="NVDA",
        risks=[
            RiskItem(
                category=RiskCategory.VALUATION,
                title="Valuation Multiple Compression",
                description=(
                    "A contraction in the valuation multiple could reduce "
                    "the expected investment return."
                ),
                severity=RiskSeverity.HIGH,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.HIGH,
                evidence=[
                    "The valuation relies on an assumed P/E multiple.",
                ],
            ),
            RiskItem(
                category=RiskCategory.INDUSTRY,
                title="Competitive Pressure",
                description=(
                    "Intensifying competition could reduce market share "
                    "or pricing power."
                ),
                severity=RiskSeverity.MEDIUM,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.MEDIUM,
                evidence=[
                    "The semiconductor industry has competitive dynamics."
                ],
            ),
        ],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=[
            "Valuation Multiple Compression",
            "Competitive Pressure",
        ],
        uncertainty_notes=[
            "Long-term demand growth remains uncertain.",
        ],
    )


def make_investment_decision() -> InvestmentDecision:
    return InvestmentDecision(
        ticker="NVDA",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=216.0,
        expected_upside=0.20,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis=(
            "The investment case is supported by strong financial "
            "performance, favorable industry conditions, and upside "
            "to the valuation target, while significant valuation "
            "and competitive risks remain."
        ),
        key_catalysts=[
            "Continued AI infrastructure investment",
            "Strong demand for accelerated computing",
        ],
        key_risks=[
            "Valuation Multiple Compression",
            "Competitive Pressure",
        ],
        invalidation_conditions=[
            "Material deterioration in growth expectations",
            "Sustained loss of competitive position",
        ],
        supporting_evidence=[
            "Strong financial performance",
            "Positive semiconductor industry outlook",
            "Valuation target above the current price",
            "Identified valuation and competitive risks",
        ],
    )


def make_input_state() -> InvestmentDecisionInputState:
    return {
        "ticker": "NVDA",
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
        "valuation": make_valuation(),
        "risk_analysis": make_risk_analysis(),
    }


def make_mock_llm(return_value=None) -> MagicMock:
    mock_llm = MagicMock()

    structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = structured_llm

    if return_value is not None:
        structured_llm.invoke.return_value = return_value

    return mock_llm


def test_investment_decision_graph_returns_structured_decision():
    expected_decision = make_investment_decision()
    mock_llm = make_mock_llm(expected_decision)

    with patch(
        "app.agents.investment_decision.llm",
        mock_llm,
    ):
        graph = build_investment_decision_graph()
        result = graph.invoke(make_input_state())

    assert result["decision_error"] is None
    assert isinstance(
        result["investment_decision"],
        InvestmentDecision,
    )

    decision = result["investment_decision"]

    assert decision.ticker == "NVDA"
    assert decision.recommendation == InvestmentRecommendation.BUY
    assert decision.investment_horizon == InvestmentHorizon.MEDIUM_TERM
    assert decision.conviction == InvestmentConviction.MEDIUM


def test_investment_decision_preserves_valuation_values():
    expected_decision = make_investment_decision()
    mock_llm = make_mock_llm(expected_decision)

    with patch(
        "app.agents.investment_decision.llm",
        mock_llm,
    ):
        graph = build_investment_decision_graph()
        result = graph.invoke(make_input_state())

    decision = result["investment_decision"]

    assert decision.current_price == 180.0
    assert decision.target_price == 216.0
    assert decision.expected_upside == 0.20


def test_investment_decision_preserves_thesis_and_evidence():
    expected_decision = make_investment_decision()
    mock_llm = make_mock_llm(expected_decision)

    with patch(
        "app.agents.investment_decision.llm",
        mock_llm,
    ):
        graph = build_investment_decision_graph()
        result = graph.invoke(make_input_state())

    decision = result["investment_decision"]

    assert decision.investment_thesis
    assert decision.key_catalysts
    assert decision.key_risks
    assert decision.invalidation_conditions
    assert decision.supporting_evidence


def test_investment_decision_graph_captures_llm_error():
    mock_llm = MagicMock()

    structured_llm = MagicMock()
    structured_llm.invoke.side_effect = RuntimeError(
        "LLM failure"
    )
    mock_llm.with_structured_output.return_value = structured_llm

    with patch(
        "app.agents.investment_decision.llm",
        mock_llm,
    ):
        graph = build_investment_decision_graph()
        result = graph.invoke(make_input_state())

    assert result["investment_decision"] is None
    assert result["decision_error"] == "LLM failure"