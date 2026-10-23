from __future__ import annotations

from app.application.errors import ApplicationErrorDetail

"""Typed state contracts for the top-level investment application graph."""

from typing import NotRequired, TypedDict

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
    # Internal long-term-memory context. Memory text is never returned publicly.
    memory_context: str
    memory_context_memory_ids: list[str]
    memory_context_error: str
    memory_capture_decision: str
    memory_capture_reason: str
    memory_capture_memory_id: str
    memory_capture_error: str
    # Research stage
    research_plan: ResearchPlan | None
    completed_research_areas: list[ResearchArea]
    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None
    research_errors: dict[str, str]
    research_data_status: str
    failed_research_areas: list[str]
    degraded_research_areas: list[str]
    research_degradation_reasons: dict[str, str]
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
    # Canonical execution lifecycle: running, completed, failed, or rejected.
    # Routing uses this field together with the stage result contract.
    execution_status: str
    stage_errors: dict[str, str]
    # 结构化错误明细：保留错误类别、是否可重试、处理责任边界等诊断信息。
    # 与 stage_errors 的区别是：stage_errors 面向快速定位，error_details 面向统一诊断与恢复策略。
    error_details: list[ApplicationErrorDetail]
    application_error: str

    # Human-in-the-loop approval
    approval_status: str
    approval_reason: str


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
    report_assembly_error: str
    report_generation_error: str
    report_merge_error: str
    report_markdown: str
    report_rendering_error: str
    research_errors: dict[str, str]
    research_data_status: str
    failed_research_areas: list[str]
    degraded_research_areas: list[str]
    research_degradation_reasons: dict[str, str]
    stage_errors: dict[str, str]
    error_details: list[ApplicationErrorDetail]
    application_error: str
    execution_status: str

    # Public approval result
    approval_status: str
    approval_reason: str
    # Safe operational metadata only; never expose retrieved memory text.
    memory_context_error: str
    memory_capture_decision: str
    memory_capture_reason: str
    memory_capture_memory_id: str
    memory_capture_error: str
