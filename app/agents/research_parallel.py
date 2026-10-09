"""Historical parallel research experiment.

Non-production module. Do not use this graph as the production Research
orchestration entry point.
"""
from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.research_state import ResearchState


def _run_company(
    state: ResearchState,
) -> ResearchState:
    result = company_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "company_research": result.get("company_research"),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }

def _run_financial(
    state: ResearchState,
) -> ResearchState:
    result = financial_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "financial_research": result.get(
            "financial_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }

def _run_market(
    state: ResearchState,
) -> ResearchState:
    result = market_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "market_research": result.get(
            "market_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }

def _run_industry_macro(
    state: ResearchState,
) -> ResearchState:
    result = industry_macro_research_graph.invoke(
        {
            "ticker": state["ticker"],
        }
    )

    return {
        "industry_macro_research": result.get(
            "industry_macro_research"
        ),
        "research_errors": result.get(
            "research_errors",
            {},
        ),
    }

def build_parallel_research_graph():
    builder = StateGraph(ResearchState)

    builder.add_node("company_research", _run_company)
    builder.add_node("financial_research", _run_financial)
    builder.add_node("market_research", _run_market)
    builder.add_node(
        "industry_macro_research",
        _run_industry_macro,
    )

    builder.add_edge(
        START,
        "company_research",
    )
    builder.add_edge(
        START,
        "financial_research",
    )
    builder.add_edge(
        START,
        "market_research",
    )
    builder.add_edge(
        START,
        "industry_macro_research",
    )

    builder.add_edge(
        "company_research",
        END,
    )
    builder.add_edge(
        "financial_research",
        END,
    )
    builder.add_edge(
        "market_research",
        END,
    )
    builder.add_edge(
        "industry_macro_research",
        END,
    )

    return builder.compile()


research_parallel_graph = build_parallel_research_graph()