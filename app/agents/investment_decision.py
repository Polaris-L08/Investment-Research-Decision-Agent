from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
)
from app.investment.models import InvestmentDecision
from app.risk.models import RiskAnalysis
from app.valuation.models import ValuationResult
from app.llm.client import llm


class InvestmentDecisionInputState(TypedDict):
    """Input contract for the investment decision graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult
    risk_analysis: RiskAnalysis


class InvestmentDecisionGraphState(TypedDict, total=False):
    """Internal state used by the investment decision graph."""

    ticker: str
    company_research: CompanyResearchResult
    financial_research: FinancialResearchResult
    market_research: MarketResearchResult
    industry_macro_research: IndustryMacroResearchResult
    valuation: ValuationResult
    risk_analysis: RiskAnalysis

    investment_decision: InvestmentDecision | None
    decision_error: str | None


class InvestmentDecisionOutputState(TypedDict):
    """Output contract for the investment decision graph."""

    investment_decision: InvestmentDecision | None
    decision_error: str | None


def make_investment_decision(
    state: InvestmentDecisionGraphState,
) -> dict:
    """Generate a structured investment decision from existing analysis."""

    structured_llm = llm.with_structured_output(InvestmentDecision)

    prompt = f"""
You are an investment decision analysis agent.

Your task is to produce a structured investment decision based ONLY
on the supplied research, valuation, and risk analysis.

You must NOT perform new web searches.
You must NOT invent facts that are not supported by the supplied evidence.
You must NOT modify the supplied valuation.
You must NOT modify the supplied risk analysis.
You must NOT perform a new valuation calculation.

Your responsibility is to synthesize the available evidence into
an investment decision.

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

Risk Analysis:
{state["risk_analysis"].model_dump_json(indent=2)}

Decision requirements:

1. Produce exactly one structured investment decision.
2. Select one recommendation from:
   - Strong Buy
   - Buy
   - Hold
   - Reduce
   - Sell
3. Select one investment horizon from:
   - Short Term
   - Medium Term
   - Long Term
4. Select one conviction level from:
   - Low
   - Medium
   - High
5. Use the supplied current price and target price.
6. Do not invent a new target price.
7. The expected upside must be mathematically consistent with
   current price and target price.
8. Summarize the investment thesis using the supplied evidence.
9. Identify the key catalysts supported by the research.
10. Identify the key risks supported by the risk analysis.
11. Identify conditions that would invalidate the investment thesis.
12. Provide supporting evidence from the supplied research,
    valuation, and risk analysis.
13. Do not produce a report.
14. Do not provide portfolio allocation or trading instructions.
"""

    try:
        investment_decision = structured_llm.invoke(prompt)

        return {
            "investment_decision": investment_decision,
            "decision_error": None,
        }

    except Exception as exc:
        return {
            "investment_decision": None,
            "decision_error": str(exc),
        }


def build_investment_decision_graph():
    """Build and compile the investment decision graph."""

    graph = StateGraph(
        InvestmentDecisionGraphState,
        input_schema=InvestmentDecisionInputState,
        output_schema=InvestmentDecisionOutputState,
    )

    graph.add_node(
        "make_investment_decision",
        make_investment_decision,
    )

    graph.add_edge(
        START,
        "make_investment_decision",
    )

    graph.add_edge(
        "make_investment_decision",
        END,
    )

    return graph.compile()

investment_decision_graph = build_investment_decision_graph()