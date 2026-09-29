from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_state import ResearchState


class ResearchFanoutInputState(TypedDict):
    ticker: str
    research_plan: ResearchPlan

class ResearchFanoutState(ResearchState, total=False):
    research_area: ResearchArea


def fan_out_research(
    state: ResearchFanoutState,
) -> list[Send]:
    plan = state["research_plan"]

    return [
        Send(
            "research_agent",
            {
                "ticker": state["ticker"],
                "research_area": research_area,
            },
        )
        for research_area in plan.research_areas
    ]

def _run_research_agent(
    state: ResearchFanoutState,
) -> ResearchFanoutState:
    research_area = state["research_area"]

    if research_area == ResearchArea.COMPANY:
        result = company_research_graph.invoke(
            {
                "ticker": state["ticker"],
            }
        )

        return {
            "company_research": result.get(
                "company_research"
            ),
            "research_errors": result.get(
                "research_errors",
                {},
            ),
        }

    if research_area == ResearchArea.FINANCIAL:
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

    if research_area == ResearchArea.MARKET:
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

    if research_area == ResearchArea.INDUSTRY_MACRO:
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

    raise ValueError(
        f"Unsupported research area: {research_area}"
    )


def build_research_fanout_graph():
    builder = StateGraph(
        ResearchFanoutState,
        input_schema=ResearchFanoutInputState,
    )

    builder.add_node(
        "research_agent",
        _run_research_agent,
    )

    builder.add_conditional_edges(
        START,
        fan_out_research,
    )

    builder.add_edge(
        "research_agent",
        END,
    )

    return builder.compile()


research_fanout_graph = build_research_fanout_graph()