from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import industry_macro_research_graph
from app.agents.market_research import market_research_graph
from app.agents.models import ResearchArea, ResearchPlan


class ResearchRouterInputState(TypedDict):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea


class ResearchRouterState(TypedDict):
    ticker: str
    research_plan: ResearchPlan
    next_research_area: ResearchArea
    routed_area: ResearchArea | None
    research_result: object | None
    research_error: str
    routing_error: str


class ResearchRouterOutputState(TypedDict):
    routed_area: ResearchArea | None
    research_result: object | None
    research_error: str
    routing_error: str


def route_research_area(state: ResearchRouterState) -> str:
    """Deterministically map a selected ResearchArea to an agent node."""
    research_area = state["next_research_area"]

    if research_area not in state["research_plan"].research_areas:
        return "routing_error"

    routes = {
        ResearchArea.COMPANY: "company_research",
        ResearchArea.FINANCIAL: "financial_research",
        ResearchArea.MARKET: "market_research",
        ResearchArea.INDUSTRY_MACRO: "industry_macro_research",
    }

    return routes[research_area]


def _run_company_research(
    state: ResearchRouterState,
) -> ResearchRouterState:
    result = company_research_graph.invoke(
        {"ticker": state["ticker"]}
    )

    return {
        "routed_area": ResearchArea.COMPANY,
        "research_result": result["research_result"],
        "research_error": result["research_error"],
        "routing_error": "",
    }


def _run_financial_research(
    state: ResearchRouterState,
) -> ResearchRouterState:
    result = financial_research_graph.invoke(
        {"ticker": state["ticker"]}
    )

    return {
        "routed_area": ResearchArea.FINANCIAL,
        "research_result": result["research_result"],
        "research_error": result["research_error"],
        "routing_error": "",
    }


def _run_market_research(
    state: ResearchRouterState,
) -> ResearchRouterState:
    result = market_research_graph.invoke(
        {"ticker": state["ticker"]}
    )

    return {
        "routed_area": ResearchArea.MARKET,
        "research_result": result["research_result"],
        "research_error": result["research_error"],
        "routing_error": "",
    }


def _run_industry_macro_research(
    state: ResearchRouterState,
) -> ResearchRouterState:
    result = industry_macro_research_graph.invoke(
        {"ticker": state["ticker"]}
    )

    return {
        "routed_area": ResearchArea.INDUSTRY_MACRO,
        "research_result": result["research_result"],
        "research_error": result["research_error"],
        "routing_error": "",
    }


def handle_routing_error(
    state: ResearchRouterState,
) -> ResearchRouterState:
    return {
        "routed_area": None,
        "research_result": None,
        "research_error": "",
        "routing_error": (
            "Research area is not included in the research plan: "
            f"{state['next_research_area'].value}"
        ),
    }


def build_research_router_graph():
    builder = StateGraph(
        ResearchRouterState,
        input_schema=ResearchRouterInputState,
        output_schema=ResearchRouterOutputState,
    )

    builder.add_node("router", lambda state: {})
    builder.add_node("company_research", _run_company_research)
    builder.add_node("financial_research", _run_financial_research)
    builder.add_node("market_research", _run_market_research)
    builder.add_node(
        "industry_macro_research",
        _run_industry_macro_research,
    )
    builder.add_node("routing_error", handle_routing_error)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_research_area,
        {
            "company_research": "company_research",
            "financial_research": "financial_research",
            "market_research": "market_research",
            "industry_macro_research": "industry_macro_research",
            "routing_error": "routing_error",
        },
    )

    builder.add_edge("company_research", END)
    builder.add_edge("financial_research", END)
    builder.add_edge("market_research", END)
    builder.add_edge("industry_macro_research", END)
    builder.add_edge("routing_error", END)

    return builder.compile()


research_router_graph = build_research_router_graph()
