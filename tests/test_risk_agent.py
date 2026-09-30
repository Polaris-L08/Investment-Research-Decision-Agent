from unittest.mock import MagicMock, patch

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.agents.risk import (
    RiskInputState,
    build_risk_graph,
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
    ValuationMethod,
    ValuationMetadata,
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
        target_price=180.0,
        current_price=180.0,
        expected_upside=0.0,
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


def make_input_state() -> RiskInputState:
    return {
        "ticker": "NVDA",
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
        "valuation": make_valuation(),
    }


def make_mock_llm(return_value=None) -> MagicMock:
    mock_llm = MagicMock()

    structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = structured_llm

    if return_value is not None:
        structured_llm.invoke.return_value = return_value

    return mock_llm


def test_risk_agent_graph_returns_structured_risk_analysis():
    expected_analysis = make_risk_analysis()
    mock_llm = make_mock_llm(expected_analysis)

    with patch("app.agents.risk.llm", mock_llm):
        graph = build_risk_graph()
        result = graph.invoke(make_input_state())

    assert result["risk_error"] is None
    assert isinstance(result["risk_analysis"], RiskAnalysis)
    assert result["risk_analysis"].ticker == "NVDA"
    assert len(result["risk_analysis"].risks) == 2
    assert result["risk_analysis"].overall_risk_level == RiskSeverity.HIGH


def test_risk_agent_graph_preserves_structured_risk_items():
    expected_analysis = make_risk_analysis()
    mock_llm = make_mock_llm(expected_analysis)

    with patch("app.agents.risk.llm", mock_llm):
        graph = build_risk_graph()
        result = graph.invoke(make_input_state())

    risks = result["risk_analysis"].risks

    assert risks[0].category == RiskCategory.VALUATION
    assert risks[0].severity == RiskSeverity.HIGH
    assert risks[0].likelihood == RiskLikelihood.MEDIUM
    assert risks[0].impact == RiskImpact.HIGH
    assert risks[0].evidence


def test_risk_agent_graph_preserves_uncertainty_notes():
    expected_analysis = make_risk_analysis()
    mock_llm = make_mock_llm(expected_analysis)

    with patch("app.agents.risk.llm", mock_llm):
        graph = build_risk_graph()
        result = graph.invoke(make_input_state())

    assert result["risk_analysis"].uncertainty_notes == [
        "Long-term demand growth remains uncertain.",
    ]


def test_risk_agent_graph_captures_llm_error():
    mock_llm = MagicMock()

    structured_llm = MagicMock()
    structured_llm.invoke.side_effect = RuntimeError("LLM failure")
    mock_llm.with_structured_output.return_value = structured_llm

    with patch("app.agents.risk.llm", mock_llm):
        graph = build_risk_graph()
        result = graph.invoke(make_input_state())

    assert result["risk_analysis"] is None
    assert result["risk_error"] == "LLM failure"
