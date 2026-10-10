"""Report Graph: assembly -> narrative generation -> format rendering."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import CompanyResearchResult, FinancialResearchResult, MarketResearchResult, \
    IndustryMacroResearchResult
from app.investment.models import InvestmentDecision
from app.report.assembly import build_investment_report
from app.report.generation import report_generation_graph
from app.report.models import InvestmentReport
from app.report.rendering import render_markdown
from app.risk.models import RiskAnalysis
from app.valuation import ValuationResult


class ReportGraphInputState(TypedDict):
    """Domain results required to assemble the final investment report."""

    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult
    risk_analysis: RiskAnalysis
    investment_decision: InvestmentDecision


class ReportGraphState(TypedDict, total=False):
    """Internal state shared by Report Graph nodes."""

    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult
    risk_analysis: RiskAnalysis
    investment_decision: InvestmentDecision
    report: InvestmentReport | None
    report_assembly_error: str
    report_generation_error: str
    report_merge_error: str
    report_markdown: str
    report_rendering_error: str


class ReportGraphOutputState(TypedDict, total=False):
    """Stable result contract returned by the Report Graph."""

    report: InvestmentReport | None
    report_assembly_error: str
    report_generation_error: str
    report_merge_error: str
    report_markdown: str
    report_rendering_error: str


def assemble_report_node(state: ReportGraphState) -> dict[str, Any]:
    """Build a structured report from upstream domain results."""

    try:
        report = build_investment_report(
            company_research=state["company_research"],
            financial_research=state["financial_research"],
            market_research=state["market_research"],
            industry_macro_research=state["industry_macro_research"],
            valuation=state["valuation"],
            risk_analysis=state["risk_analysis"],
            investment_decision=state["investment_decision"],
        )
        return {
            "report": report,
            "report_assembly_error": "",
        }
    except Exception as exc:
        return {
            "report": None,
            "report_assembly_error": str(exc) or type(exc).__name__,
        }


def route_after_assembly(state: ReportGraphState) -> str:
    if state.get("report") is not None and not state.get("report_assembly_error"):
        return "continue"
    return "end"


def generate_report_node(state: ReportGraphState) -> dict[str, Any]:
    """Generate narrative while retaining the deterministic report on failure."""

    report = state.get("report")
    if report is None:
        return {
            "report_generation_error": "Report is required before narrative generation.",
            "report_merge_error": "",
        }

    try:
        raw = report_generation_graph.invoke({"report": report})
        if not isinstance(raw, Mapping):
            raise TypeError("Report generation output must be a mapping.")

        generation_error = raw.get("generation_error")
        merge_error = raw.get("merge_error")
        for field_name, value in (
            ("generation_error", generation_error),
            ("merge_error", merge_error),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"Report {field_name} must be a string or None.")

        generated_report = raw.get("report")
        if generated_report is None and not generation_error and not merge_error:
            raise TypeError(
                "Report generation returned no report and no explicit error."
            )
        if generated_report is None:
            generated_report = report
        if not isinstance(generated_report, InvestmentReport):
            raise TypeError("Report generation result must be an InvestmentReport.")

        return {
            "report": generated_report,
            "report_generation_error": generation_error or "",
            "report_merge_error": merge_error or "",
        }
    except Exception as exc:
        return {
            "report": report,
            "report_generation_error": str(exc) or type(exc).__name__,
            "report_merge_error": "",
        }


def render_report_node(state: ReportGraphState) -> dict[str, Any]:
    """Render the final or fallback report as Markdown."""
    report = state.get("report")
    if report is None:
        return {
            "report_markdown": "",
            "report_rendering_error": "Report is required before rendering.",
        }
    try:
        return {
            "report_markdown": render_markdown(report),
            "report_rendering_error": "",
        }
    except Exception as exc:
        return {
            "report_markdown": "",
            "report_rendering_error": str(exc) or type(exc).__name__,
        }


def build_report_graph():
    """Compile the Report Graph; output formats can be extended when needed."""

    builder = StateGraph(
        ReportGraphState,
        input_schema=ReportGraphInputState,
        output_schema=ReportGraphOutputState,
    )
    builder.add_node("report_assembly", assemble_report_node)
    builder.add_node("report_generation", generate_report_node)
    builder.add_node("report_rendering", render_report_node)

    builder.add_edge(START, "report_assembly")
    builder.add_conditional_edges(
        "report_assembly",
        route_after_assembly,
        {"continue": "report_generation", "end": END},
    )
    builder.add_edge("report_generation", "report_rendering")
    builder.add_edge("report_rendering", END)
    return builder.compile()


report_graph = build_report_graph()