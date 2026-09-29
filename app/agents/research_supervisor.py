from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_state import ResearchState


class ResearchSupervisorInputState(TypedDict):
    ticker: str
    research_plan: ResearchPlan


class ResearchSupervisorState(ResearchState, total=False):
    completed_research_areas: list[ResearchArea]
    current_research_area: ResearchArea | None
    supervisor_error: str


class ResearchSupervisorOutputState(
    ResearchState,
    total=False,
):
    completed_research_areas: list[ResearchArea]
    current_research_area: ResearchArea | None
    supervisor_error: str


def select_next_research_area(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Select the next research area that has not been completed."""

    plan = state["research_plan"]

    completed = set(
        state.get("completed_research_areas", [])
    )

    for research_area in plan.research_areas:
        if research_area not in completed:
            return {
                "current_research_area": research_area,
                "supervisor_error": "",
            }

    return {
        "current_research_area": None,
        "supervisor_error": "",
    }


def route_and_execute(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Execute the research agent for the current research area."""

    research_area = state.get("current_research_area")

    if research_area is None:
        return {
            "supervisor_error": (
                "No current research area is available."
            ),
        }

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

    return {
        "supervisor_error": (
            f"Unsupported research area: {research_area}"
        ),
    }


def mark_completed(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Mark the current research area as completed."""

    current = state.get("current_research_area")

    if current is None:
        return {
            "supervisor_error": (
                "No current research area to mark as completed."
            ),
        }

    completed = list(
        state.get("completed_research_areas", [])
    )

    if current not in completed:
        completed.append(current)

    return {
        "completed_research_areas": completed,
        "current_research_area": None,
        "supervisor_error": "",
    }


def supervisor_should_continue(
    state: ResearchSupervisorState,
) -> str:
    """Decide whether the supervisor should execute or finish."""

    if state.get("supervisor_error"):
        return "error"

    if state.get("current_research_area") is None:
        return "done"

    return "execute"


def build_research_supervisor_graph():
    """Build the research supervisor graph."""

    builder = StateGraph(
        ResearchSupervisorState,
        input_schema=ResearchSupervisorInputState,
        output_schema=ResearchSupervisorOutputState,
    )

    builder.add_node(
        "supervisor",
        select_next_research_area,
    )

    builder.add_node(
        "route_and_execute",
        route_and_execute,
    )

    builder.add_node(
        "mark_completed",
        mark_completed,
    )

    builder.add_edge(
        START,
        "supervisor",
    )

    builder.add_conditional_edges(
        "supervisor",
        supervisor_should_continue,
        {
            "execute": "route_and_execute",
            "done": END,
            "error": END,
        },
    )

    builder.add_edge(
        "route_and_execute",
        "mark_completed",
    )

    builder.add_edge(
        "mark_completed",
        "supervisor",
    )

    return builder.compile()


research_supervisor_graph = (
    build_research_supervisor_graph()
)