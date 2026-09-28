from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_planner import research_planner_graph
from app.agents.research_router import research_router_graph
from app.agents.research_state import ResearchState


RESEARCH_ORDER = [
    ResearchArea.COMPANY,
    ResearchArea.FINANCIAL,
    ResearchArea.MARKET,
    ResearchArea.INDUSTRY_MACRO,
]


class ResearchOrchestratorInputState(TypedDict):
    user_query: str
    ticker: str


class ResearchOrchestratorState(ResearchState, total=False):
    user_query: str

    # Router output
    routed_area: ResearchArea | None
    routing_error: str

    # Sequential orchestration
    completed_research_areas: list[ResearchArea]
    current_research_area: ResearchArea | None

    # Planner / orchestration errors
    planning_error: str
    orchestration_error: str


class ResearchOrchestratorOutputState(
    ResearchState,
    total=False,
):
    routed_area: ResearchArea | None
    routing_error: str
    planning_error: str
    orchestration_error: str


def _plan_research(
    state: ResearchOrchestratorState,
) -> ResearchOrchestratorState:
    result = research_planner_graph.invoke(
        {"user_query": state["user_query"]}
    )

    return {
        "research_plan": result["research_plan"],
        "planning_error": result["planning_error"],
    }


def _prepare_next_research(
    state: ResearchOrchestratorState,
) -> ResearchOrchestratorState:
    plan = state.get("research_plan")
    completed = state.get("completed_research_areas", [])

    if plan is None:
        return {
            "current_research_area": None,
            "orchestration_error": "Research plan is unavailable.",
        }

    for research_area in RESEARCH_ORDER:
        if (
            research_area in plan.research_areas
            and research_area not in completed
        ):
            return {"current_research_area": research_area}

    return {"current_research_area": None}


def _route_and_execute(
    state: ResearchOrchestratorState,
) -> ResearchOrchestratorState:
    research_area = state["current_research_area"]

    if research_area is None:
        return {}

    result = research_router_graph.invoke(
        {
            **state,
            "next_research_area": research_area,
        }
    )

    return {
        "routed_area": result.get("routed_area"),
        "company_research": result.get("company_research"),
        "financial_research": result.get("financial_research"),
        "market_research": result.get("market_research"),
        "industry_macro_research": result.get(
            "industry_macro_research"
        ),
        "research_errors": result.get(
            "research_errors",
            state.get("research_errors", {}),
        ),
        "routing_error": result.get("routing_error", ""),
    }


def _mark_completed(
    state: ResearchOrchestratorState,
) -> ResearchOrchestratorState:
    research_area = state.get("current_research_area")
    completed = list(state.get("completed_research_areas", []))

    if research_area is not None and research_area not in completed:
        completed.append(research_area)

    return {
        "completed_research_areas": completed,
        "current_research_area": None,
    }


def _route_after_execution(
    state: ResearchOrchestratorState,
) -> str:
    if state.get("routing_error"):
        return "orchestration_error"

    if state.get("planning_error"):
        return "orchestration_error"

    return "prepare_next_research"


def _route_after_prepare(
    state: ResearchOrchestratorState,
) -> str:
    if state.get("orchestration_error"):
        return "orchestration_error"

    if state.get("current_research_area") is None:
        return "done"

    return "route_and_execute"


def _handle_orchestration_error(
    state: ResearchOrchestratorState,
) -> ResearchOrchestratorState:
    return {
        "orchestration_error": (
            state.get("orchestration_error")
            or state.get("routing_error")
            or state.get("planning_error")
            or "Research orchestration failed."
        )
    }


def build_research_orchestrator_graph():
    builder = StateGraph(
        ResearchOrchestratorState,
        input_schema=ResearchOrchestratorInputState,
        output_schema=ResearchOrchestratorOutputState,
    )

    builder.add_node("research_planner", _plan_research)
    builder.add_node("prepare_next_research", _prepare_next_research)
    builder.add_node("route_and_execute", _route_and_execute)
    builder.add_node("mark_completed", _mark_completed)
    builder.add_node(
        "orchestration_error",
        _handle_orchestration_error,
    )

    builder.add_edge(START, "research_planner")
    builder.add_conditional_edges(
        "research_planner",
        lambda state: (
            "orchestration_error"
            if state.get("planning_error")
            else "prepare_next_research"
        ),
        {
            "prepare_next_research": "prepare_next_research",
            "orchestration_error": "orchestration_error",
        },
    )

    builder.add_conditional_edges(
        "prepare_next_research",
        _route_after_prepare,
        {
            "route_and_execute": "route_and_execute",
            "done": END,
            "orchestration_error": "orchestration_error",
        },
    )

    builder.add_edge("route_and_execute", "mark_completed")
    builder.add_conditional_edges(
        "mark_completed",
        _route_after_execution,
        {
            "prepare_next_research": "prepare_next_research",
            "orchestration_error": "orchestration_error",
        },
    )

    builder.add_edge("orchestration_error", END)

    return builder.compile()


research_orchestrator_graph = build_research_orchestrator_graph()
