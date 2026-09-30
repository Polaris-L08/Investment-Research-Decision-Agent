import pytest

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
from app.report.assembly import build_investment_report
from app.report.models import InvestmentReport
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


def make_company_research(
    ticker: str = "NVDA",
) -> CompanyResearchResult:
    return CompanyResearchResult(
        ticker=ticker,
        company_name="NVIDIA Corporation",
        sector="Semiconductors",
        current_price=180.0,
        summary=(
            "NVIDIA designs GPUs and accelerated computing platforms."
        ),
    )


def make_financial_research(
    ticker: str = "NVDA",
) -> FinancialResearchResult:
    return FinancialResearchResult(
        ticker=ticker,
        revenue=100.0,
        net_income=30.0,
        profit_margin=0.30,
        summary="The company has strong financial performance.",
    )


def make_market_research(
    ticker: str = "NVDA",
) -> MarketResearchResult:
    return MarketResearchResult(
        ticker=ticker,
        market_index="NASDAQ",
        market_return=0.08,
        summary="The broader technology market remains positive.",
    )


def make_industry_macro_research(
    ticker: str = "NVDA",
) -> IndustryMacroResearchResult:
    return IndustryMacroResearchResult(
        ticker=ticker,
        industry="Semiconductors",
        industry_growth=0.15,
        macro_environment="Growth-oriented technology environment",
        macro_growth=0.03,
        summary="AI infrastructure supports semiconductor demand.",
    )


def make_valuation(
    ticker: str = "NVDA",
) -> ValuationResult:
    return ValuationResult(
        ticker=ticker,
        method=ValuationMethod.PE,
        inputs=ValuationInputs(
            earnings_per_share=6.0,
        ),
        assumptions=ValuationAssumptions(
            multiple=36.0,
            rationale="Illustrative P/E multiple assumption.",
        ),
        implied_value_per_share=216.0,
        target_price=216.0,
        current_price=180.0,
        expected_upside=0.20,
        metadata=ValuationMetadata(
            currency="USD",
            model_version="phase7-v1",
        ),
    )


def make_risk_analysis(
    ticker: str = "NVDA",
) -> RiskAnalysis:
    return RiskAnalysis(
        ticker=ticker,
        risks=[
            RiskItem(
                category=RiskCategory.VALUATION,
                title="Valuation Multiple Compression",
                description=(
                    "A contraction in the valuation multiple "
                    "could reduce expected returns."
                ),
                severity=RiskSeverity.HIGH,
                likelihood=RiskLikelihood.MEDIUM,
                impact=RiskImpact.HIGH,
                evidence=[
                    "The valuation relies on an assumed P/E multiple."
                ],
            )
        ],
        overall_risk_level=RiskSeverity.HIGH,
        key_risks=[
            "Valuation Multiple Compression",
        ],
        uncertainty_notes=[
            "Long-term demand remains uncertain.",
        ],
    )


def make_investment_decision(
    ticker: str = "NVDA",
    key_risks: list[str] | None = None,
) -> InvestmentDecision:
    if key_risks is None:
        key_risks = [
            "Valuation Multiple Compression",
        ]

    return InvestmentDecision(
        ticker=ticker,
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=216.0,
        expected_upside=0.20,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis=(
            "Strong financial performance and industry conditions "
            "support the investment thesis."
        ),
        key_catalysts=[
            "Continued AI infrastructure investment",
        ],
        key_risks=key_risks,
        invalidation_conditions=[
            "Material deterioration in growth expectations",
        ],
        supporting_evidence=[
            "Strong financial performance",
            "Valuation target above current price",
        ],
    )


def build_inputs():
    return {
        "company_research": make_company_research(),
        "financial_research": make_financial_research(),
        "market_research": make_market_research(),
        "industry_macro_research": make_industry_macro_research(),
        "valuation": make_valuation(),
        "risk_analysis": make_risk_analysis(),
        "investment_decision": make_investment_decision(),
    }


def test_build_investment_report_returns_report():
    report = build_investment_report(**build_inputs())

    assert isinstance(report, InvestmentReport)
    assert report.ticker == "NVDA"


def test_build_investment_report_maps_research_summaries():
    report = build_investment_report(**build_inputs())

    assert report.company_overview == (
        "NVIDIA designs GPUs and accelerated computing platforms."
    )
    assert report.financial_summary == (
        "The company has strong financial performance."
    )
    assert report.market_summary == (
        "The broader technology market remains positive."
    )
    assert report.industry_macro_summary == (
        "AI infrastructure supports semiconductor demand."
    )


def test_build_investment_report_preserves_domain_objects():
    inputs = build_inputs()

    report = build_investment_report(**inputs)

    assert report.valuation is inputs["valuation"]
    assert report.risk_analysis is inputs["risk_analysis"]
    assert report.investment_decision is inputs["investment_decision"]


def test_build_investment_report_preserves_phase7_facts():
    report = build_investment_report(**build_inputs())

    assert report.valuation.current_price == 180.0
    assert report.valuation.target_price == 216.0
    assert report.valuation.expected_upside == 0.20

    assert (
        report.investment_decision.recommendation
        == InvestmentRecommendation.BUY
    )
    assert (
        report.investment_decision.investment_horizon
        == InvestmentHorizon.MEDIUM_TERM
    )
    assert (
        report.investment_decision.conviction
        == InvestmentConviction.MEDIUM
    )

    assert report.risk_analysis.key_risks == [
        "Valuation Multiple Compression",
    ]


def test_build_investment_report_rejects_ticker_mismatch():
    inputs = build_inputs()
    inputs["valuation"] = make_valuation(ticker="AAPL")

    with pytest.raises(ValueError, match="ticker"):
        build_investment_report(**inputs)


def test_build_investment_report_rejects_valuation_decision_mismatch():
    inputs = build_inputs()

    inputs["investment_decision"] = InvestmentDecision(
        ticker="NVDA",
        recommendation=InvestmentRecommendation.BUY,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM,
        current_price=180.0,
        target_price=225.0,
        expected_upside=0.25,
        conviction=InvestmentConviction.MEDIUM,
        investment_thesis="Test thesis.",
        key_catalysts=["Test catalyst."],
        key_risks=["Valuation Multiple Compression"],
        invalidation_conditions=["Test invalidation."],
        supporting_evidence=["Test evidence."],
    )

    with pytest.raises(
        ValueError,
        match="target_price",
    ):
        build_investment_report(**inputs)


def test_build_investment_report_rejects_risk_decision_mismatch():
    inputs = build_inputs()

    inputs["investment_decision"] = make_investment_decision(
        key_risks=["Different risk"],
    )

    with pytest.raises(
        ValueError,
        match="key_risks",
    ):
        build_investment_report(**inputs)