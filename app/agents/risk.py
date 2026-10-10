from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.llm.client import llm
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult


class RiskInputState(TypedDict):
    """Input contract for the risk analysis graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult


class RiskGraphState(TypedDict, total=False):
    """Internal state used by the risk analysis graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult

    risk_analysis: RiskAnalysis | None
    risk_error: str | None


class RiskOutputState(TypedDict):
    """Output contract for the risk analysis graph."""

    risk_analysis: RiskAnalysis | None
    risk_error: str | None


def analyze_risk(state: RiskGraphState) -> dict:
    """Analyze investment risks from existing research and valuation."""

    structured_risk_llm = llm.with_structured_output(RiskAnalysis)

    prompt = f"""
You are an investment risk analysis agent.

Your task is to analyze the existing research and valuation evidence
and identify the major risks that could affect the investment thesis.

You must NOT perform new web searches.
You must NOT invent facts that are not supported by the supplied evidence.
You must NOT generate an investment recommendation.
You must only produce a structured risk analysis.

Ticker:
{state["ticker"]}

Company Research:
{state["company_research"].model_dump_json(indent=2)}

Financial Research:
{state["financial_research"].model_dump_json(indent=2)}

Market Research:
{state["market_research"].model_dump_json(indent=2)}

Industry / Macro Research:
{state["industry_macro_research"].model_dump_json(indent=2)}

Valuation:
{state["valuation"].model_dump_json(indent=2)}

Risk analysis requirements:

1. Identify material risks relevant to the investment thesis.
2. Classify each risk using the available risk categories.
3. Assess likelihood, impact, and severity using the defined enums.
4. Provide evidence supporting each identified risk.
5. Highlight the most important risks in key_risks.
6. Explicitly identify important uncertainties or limitations in
   uncertainty_notes.
7. Do not generate Buy, Sell, Hold, or any other investment recommendation.
8. Do not create a new target price or modify the supplied valuation.
"""

    try:
        risk_analysis = structured_risk_llm.invoke(prompt)

        return {
            "risk_analysis": risk_analysis,
            "risk_error": None,
        }

    except Exception as exc:
        return {
            "risk_analysis": None,
            "risk_error": str(exc),
        }


def build_risk_graph():
    """Build and compile the risk analysis graph."""

    graph = StateGraph(
        RiskGraphState,
        input_schema=RiskInputState,
        output_schema=RiskOutputState,
    )

    graph.add_node("analyze_risk", analyze_risk)

    graph.add_edge(START, "analyze_risk")
    graph.add_edge("analyze_risk", END)

    return graph.compile()

risk_graph = build_risk_graph()