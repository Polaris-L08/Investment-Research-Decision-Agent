from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.investment.models import InvestmentDecision
from app.report.models import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


def _validate_ticker_consistency(
    ticker: str,
    company_research: CompanyResearchResult,
    financial_research: FinancialResearchResult,
    market_research: MarketResearchResult,
    industry_macro_research: IndustryMacroResearchResult,
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> None:
    """Ensure every Phase 7 result belongs to the same investment."""

    sources = {
        "company_research": company_research.ticker,
        "financial_research": financial_research.ticker,
        "market_research": market_research.ticker,
        "industry_macro_research": industry_macro_research.ticker,
        "valuation": valuation.ticker,
        "risk_analysis": risk_analysis.ticker,
        "investment_decision": investment_decision.ticker,
    }

    mismatches = {
        name: source_ticker
        for name, source_ticker in sources.items()
        if source_ticker != ticker
    }

    if mismatches:
        details = ", ".join(
            f"{name}={source_ticker}"
            for name, source_ticker in mismatches.items()
        )
        raise ValueError(
            f"All report inputs must use ticker '{ticker}'. "
            f"Mismatched inputs: {details}"
        )


def _validate_cross_domain_contract(
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> None:
    """Ensure cross-domain contracts remain consistent."""

    if (
        valuation.current_price
        != investment_decision.current_price
    ):
        raise ValueError(
            "Valuation current_price must match "
            "InvestmentDecision current_price."
        )

    if valuation.target_price != investment_decision.target_price:
        raise ValueError(
            "Valuation target_price must match "
            "InvestmentDecision target_price."
        )

    if valuation.expected_upside != investment_decision.expected_upside:
        raise ValueError(
            "Valuation expected_upside must match "
            "InvestmentDecision expected_upside."
        )

    if risk_analysis.key_risks != investment_decision.key_risks:
        raise ValueError(
            "RiskAnalysis key_risks must match "
            "InvestmentDecision key_risks."
        )


def build_investment_report(
    company_research: CompanyResearchResult,
    financial_research: FinancialResearchResult,
    market_research: MarketResearchResult,
    industry_macro_research: IndustryMacroResearchResult,
    valuation: ValuationResult,
    risk_analysis: RiskAnalysis,
    investment_decision: InvestmentDecision,
) -> InvestmentReport:
    """
    Deterministically assemble Phase 7 results into an InvestmentReport.

    This function does not create new business facts. It only validates
    existing cross-domain contracts and maps existing results into the
    report domain.
    """

    ticker = investment_decision.ticker

    _validate_ticker_consistency(
        ticker=ticker,
        company_research=company_research,
        financial_research=financial_research,
        market_research=market_research,
        industry_macro_research=industry_macro_research,
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )

    _validate_cross_domain_contract(
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )

    return InvestmentReport(
        ticker=ticker,
        title=f"{ticker} Investment Research Report",
        executive_summary=investment_decision.investment_thesis,
        company_overview=company_research.summary,
        financial_summary=financial_research.summary,
        market_summary=market_research.summary,
        industry_macro_summary=industry_macro_research.summary,
        valuation_summary=(
            f"Valuation target price: "
            f"{valuation.target_price:.2f}; "
            f"current price: "
            f"{valuation.current_price:.2f}; "
            f"expected upside: "
            f"{valuation.expected_upside:.2%}."
        ),
        risk_summary=(
            f"Overall risk level: "
            f"{risk_analysis.overall_risk_level.value}. "
            f"Key risks: "
            f"{', '.join(risk_analysis.key_risks)}."
        ),
        investment_decision_summary=(
            f"Recommendation: "
            f"{investment_decision.recommendation.value}; "
            f"horizon: "
            f"{investment_decision.investment_horizon.value}; "
            f"conviction: "
            f"{investment_decision.conviction.value}."
        ),
        valuation=valuation,
        risk_analysis=risk_analysis,
        investment_decision=investment_decision,
    )