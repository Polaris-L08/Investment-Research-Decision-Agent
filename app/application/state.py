from __future__ import annotations

"""Production Application workflow state and public contracts.

This module defines the shared data boundary for the future top-level
Application Graph. It intentionally does not implement graph orchestration.
"""

from typing import TypedDict, NotRequired

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchPlan,
    ResearchArea,
)
from app.investment.models import InvestmentDecision

from app.report.models import InvestmentReport
from app.risk.models import RiskAnalysis
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationResult,
)


class ApplicationInputState(TypedDict):
    """Minimum caller-provided input to start an investment analysis."""

    ticker: str
    user_query: str
    valuation_inputs: NotRequired[ValuationInputs]
    valuation_assumptions: NotRequired[ValuationAssumptions]

class ApplicationState(TypedDict, total=False):
    """Shared state owned by the production Application workflow."""

    # Request context
    ticker: str
    user_query: str

    # Research stage
    research_plan: ResearchPlan | None
    completed_research_areas: list[ResearchArea]
    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None
    research_errors: dict[str, str]
    planning_error: str
    supervisor_error: str

    # Valuation boundary and result
    valuation_inputs: ValuationInputs | None
    valuation_assumptions: ValuationAssumptions | None
    valuation: ValuationResult | None
    valuation_error: str

    # Risk stage
    risk_analysis: RiskAnalysis | None
    risk_error: str

    # Investment decision stage
    investment_decision: InvestmentDecision | None
    decision_error: str

    # Report stage
    report: InvestmentReport | None
    report_assembly_error: str
    report_generation_error: str
    report_merge_error: str
    report_markdown: str
    report_rendering_error: str

    # Workflow control and normalized error collection
    current_stage: str
    stage_errors: dict[str, str]
    application_error: str


class ApplicationOutputState(TypedDict, total=False):
    """Stable public result returned by the production Application Graph."""

    ticker: str
    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None
    valuation: ValuationResult | None
    valuation_error: str
    risk_analysis: RiskAnalysis | None
    risk_error: str
    investment_decision: InvestmentDecision | None
    decision_error: str
    report: InvestmentReport | None
    research_errors: dict[str, str]
    stage_errors: dict[str, str]
    report_assembly_error: str
    report_generation_error: str
    report_merge_error: str
    report_markdown: str
    report_rendering_error: str
    application_error: str
