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
from app.agents.risk import (
    RiskInputState,
    build_risk_graph,
)
from app.agents.valuation import valuation_graph
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
        macro_environment=(
            "Growth-oriented technology investment environment"
        ),
        macro_growth=0.03,
        summary=(
            "The semiconductor industry benefits from AI infrastructure "
            "investment but remains exposed to macroeconomic conditions."
        ),
    )


def make_valuation_inputs() -> ValuationInputs:
    return ValuationInputs(
        earnings_per_share=6.0,
    )


def make_valuation_assumptions() -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=36.0,
        rationale="Illustrative P/E multiple assumption.",
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


def make_mock_llm(return_value) -> MagicMock:
    mock_llm = MagicMock()

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = return_value

    mock_llm.with_structured_output.return_value = structured_llm

    return mock_llm


def build_research_state():
    return {
        "ticker": "NVDA",
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
    }


def test_phase7_research_to_valuation_contract():
    research_state = build_research_state()

    result = valuation_graph.invoke(
        {
            "ticker": research_state["ticker"],
            "company_research": research_state["company_research"],
            "valuation_inputs": make_valuation_inputs(),
            "valuation_assumptions": make_valuation_assumptions(),
        }
    )

    assert result["valuation_error"] == ""
    assert result["valuation_analysis"] is not None

    valuation = result["valuation_analysis"]

    assert valuation.ticker == "NVDA"
    assert valuation.current_price == 180.0
    assert valuation.target_price == 216.0
    assert valuation.expected_upside == 0.20


def test_phase7_valuation_to_risk_contract():
    research_state = build_research_state()

    valuation_result = valuation_graph.invoke(
        {
            "ticker": research_state["ticker"],
            "company_research": research_state["company_research"],
            "valuation_inputs": make_valuation_inputs(),
            "valuation_assumptions": make_valuation_assumptions(),
        }
    )

    valuation = valuation_result["valuation_analysis"]

    expected_risk = make_risk_analysis()
    mock_llm = make_mock_llm(expected_risk)

    risk_input: RiskInputState = {
        "ticker": research_state["ticker"],
        "company_research": research_state["company_research"],
        "financial_research": research_state["financial_research"],
        "market_research": research_state["market_research"],
        "industry_macro_research": research_state[
            "industry_macro_research"
        ],
        "valuation": valuation,
    }

    with patch(
        "app.agents.risk.llm",
        mock_llm,
    ):
        risk_graph = build_risk_graph()
        result = risk_graph.invoke(risk_input)

    assert result["risk_error"] is None
    assert isinstance(result["risk_analysis"], RiskAnalysis)

    risk_analysis = result["risk_analysis"]

    assert risk_analysis.ticker == valuation.ticker
    assert risk_analysis.overall_risk_level == RiskSeverity.HIGH
    assert risk_analysis.key_risks


def test_phase7_risk_to_decision_contract():
    research_state = build_research_state()

    valuation_result = valuation_graph.invoke(
        {
            "ticker": research_state["ticker"],
            "company_research": research_state["company_research"],
            "valuation_inputs": make_valuation_inputs(),
            "valuation_assumptions": make_valuation_assumptions(),
        }
    )

    valuation = valuation_result["valuation_analysis"]

    risk_analysis = make_risk_analysis()
    expected_decision = make_investment_decision()

    mock_llm = make_mock_llm(expected_decision)

    decision_input: InvestmentDecisionInputState = {
        "ticker": research_state["ticker"],
        "company_research": research_state["company_research"],
        "financial_research": research_state["financial_research"],
        "market_research": research_state["market_research"],
        "industry_macro_research": research_state[
            "industry_macro_research"
        ],
        "valuation": valuation,
        "risk_analysis": risk_analysis,
    }

    with patch(
        "app.agents.investment_decision.llm",
        mock_llm,
    ):
        decision_graph = build_investment_decision_graph()
        result = decision_graph.invoke(decision_input)

    assert result["decision_error"] is None
    assert isinstance(
        result["investment_decision"],
        InvestmentDecision,
    )

    decision = result["investment_decision"]

    assert decision.ticker == risk_analysis.ticker
    assert decision.current_price == valuation.current_price
    assert decision.target_price == valuation.target_price
    assert decision.expected_upside == valuation.expected_upside

    assert decision.recommendation == (
        InvestmentRecommendation.BUY
    )
    assert decision.investment_horizon == (
        InvestmentHorizon.MEDIUM_TERM
    )
    assert decision.conviction == InvestmentConviction.MEDIUM

    assert decision.key_risks == risk_analysis.key_risks
    assert decision.investment_thesis
    assert decision.supporting_evidence


def test_phase7_full_data_contract_chain():
    research_state = build_research_state()

    # ---------------------------------------------------------
    # Step 1: Research → Valuation
    # ---------------------------------------------------------

    valuation_result = valuation_graph.invoke(
        {
            "ticker": research_state["ticker"],
            "company_research": research_state["company_research"],
            "valuation_inputs": make_valuation_inputs(),
            "valuation_assumptions": make_valuation_assumptions(),
        }
    )

    assert valuation_result["valuation_error"] == ""

    valuation = valuation_result["valuation_analysis"]

    assert valuation is not None

    # ---------------------------------------------------------
    # Step 2: Research + Valuation → Risk
    # ---------------------------------------------------------

    risk_analysis = make_risk_analysis()
    risk_llm = make_mock_llm(risk_analysis)

    risk_input: RiskInputState = {
        "ticker": research_state["ticker"],
        "company_research": research_state["company_research"],
        "financial_research": research_state["financial_research"],
        "market_research": research_state["market_research"],
        "industry_macro_research": research_state[
            "industry_macro_research"
        ],
        "valuation": valuation,
    }

    with patch(
        "app.agents.risk.llm",
        risk_llm,
    ):
        risk_graph = build_risk_graph()
        risk_result = risk_graph.invoke(risk_input)

    assert risk_result["risk_error"] is None

    produced_risk = risk_result["risk_analysis"]

    assert produced_risk is not None
    assert produced_risk.ticker == valuation.ticker

    # ---------------------------------------------------------
    # Step 3: Research + Valuation + Risk → Decision
    # ---------------------------------------------------------

    expected_decision = make_investment_decision()
    decision_llm = make_mock_llm(expected_decision)

    decision_input: InvestmentDecisionInputState = {
        "ticker": research_state["ticker"],
        "company_research": research_state["company_research"],
        "financial_research": research_state["financial_research"],
        "market_research": research_state["market_research"],
        "industry_macro_research": research_state[
            "industry_macro_research"
        ],
        "valuation": valuation,
        "risk_analysis": produced_risk,
    }

    with patch(
        "app.agents.investment_decision.llm",
        decision_llm,
    ):
        decision_graph = build_investment_decision_graph()
        decision_result = decision_graph.invoke(decision_input)

    assert decision_result["decision_error"] is None

    decision = decision_result["investment_decision"]

    assert isinstance(decision, InvestmentDecision)

    # ---------------------------------------------------------
    # Cross-domain contract assertions
    # ---------------------------------------------------------

    assert decision.ticker == research_state["ticker"]

    assert (
        valuation.current_price
        == research_state["company_research"].current_price
    )

    assert decision.current_price == valuation.current_price
    assert decision.target_price == valuation.target_price
    assert decision.expected_upside == valuation.expected_upside

    assert decision.key_risks == produced_risk.key_risks

    assert decision.investment_thesis
    assert decision.supporting_evidence