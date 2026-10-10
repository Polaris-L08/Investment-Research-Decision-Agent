from typing import TypedDict, Annotated

from langgraph.graph import END, START, StateGraph

from app.agents.company_research import company_research_graph
from app.agents.financial_research import financial_research_graph
from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.market_research import market_research_graph
from app.agents.models import ResearchArea, ResearchPlan, CompanyResearchResult, FinancialResearchResult, \
    MarketResearchResult, IndustryMacroResearchResult
from app.agents.research_planner import research_planner_graph
from app.agents.research_state import merge_research_errors
from app.providers.runtime import get_provider_bundle
from app.valuation import ValuationAssumptions, ValuationInputs


class ResearchSupervisorInputState(TypedDict):
    """Public input contract for the complete Research stage."""

    ticker: str
    user_query: str


class ResearchSupervisorState(TypedDict, total=False):
    """Internal state owned by ResearchSupervisor."""

    ticker: str
    user_query: str
    research_plan: ResearchPlan | None

    next_research_area: ResearchArea | None
    completed_research_areas: list[ResearchArea]

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: Annotated[
        dict[str, str],
        merge_research_errors,
    ]
    planning_error: str
    supervisor_error: str

    valuation_inputs: ValuationInputs | None
    valuation_assumptions: ValuationAssumptions | None
    valuation_research_error: str


class ResearchSupervisorOutputState(TypedDict, total=False):
    """Stable output contract returned to the parent application graph."""

    ticker: str
    research_plan: ResearchPlan | None
    completed_research_areas: list[ResearchArea]

    company_research: CompanyResearchResult | None
    financial_research: FinancialResearchResult | None
    market_research: MarketResearchResult | None
    industry_macro_research: IndustryMacroResearchResult | None

    research_errors: dict[str, str]
    planning_error: str
    supervisor_error: str
    valuation_inputs: ValuationInputs | None
    valuation_assumptions: ValuationAssumptions | None
    valuation_research_error: str


def plan_research(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Create the research plan inside the Supervisor boundary."""

    ticker = state.get("ticker", "").strip()
    if not ticker:
        message = "Ticker is required for research execution."
        return {
            "research_plan": None,
            "planning_error": "",
            "supervisor_error": message,
        }

    user_query = state.get("user_query", "").strip()
    if not user_query:
        message = "User query is required for research planning."
        return {
            "research_plan": None,
            "planning_error": message,
            "supervisor_error": message,
        }

    try:
        result = research_planner_graph.invoke(
            {"user_query": user_query}
        )
    except Exception as exc:
        message = f"Research planner invocation failed: {exc}"
        return {
            "research_plan": None,
            "planning_error": message,
            "supervisor_error": message,
        }

    research_plan = result.get("research_plan")
    planning_error = result.get("planning_error", "")

    if planning_error or research_plan is None:
        message = planning_error or "Research planner returned no plan."
        return {
            "research_plan": research_plan,
            "planning_error": message,
            "supervisor_error": message,
        }

    return {
        "research_plan": research_plan,
        "planning_error": "",
        "supervisor_error": "",
    }


def select_next_research_area(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Select the next uncompleted area in the planner's requested order."""

    if state.get("planning_error") or state.get("supervisor_error"):
        return {"next_research_area": None}

    plan = state.get("research_plan")
    if plan is None:
        return {
            "next_research_area": None,
            "supervisor_error": "Research plan is unavailable.",
        }

    completed = set(state.get("completed_research_areas", []))

    for research_area in plan.research_areas:
        if research_area not in completed:
            return {"next_research_area": research_area}

    return {"next_research_area": None}


def route_and_execute(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Execute the research agent for the current research area."""

    research_area = state.get("next_research_area")

    if research_area is None:
        return {
            "supervisor_error": (
                "No research area was selected for execution."
            ),
        }

    child_graphs = {
        ResearchArea.COMPANY: company_research_graph,
        ResearchArea.FINANCIAL: financial_research_graph,
        ResearchArea.MARKET: market_research_graph,
        ResearchArea.INDUSTRY_MACRO: industry_macro_research_graph,
    }
    result_fields = {
        ResearchArea.COMPANY: "company_research",
        ResearchArea.FINANCIAL: "financial_research",
        ResearchArea.MARKET: "market_research",
        ResearchArea.INDUSTRY_MACRO: "industry_macro_research",
    }

    child_graph = child_graphs.get(research_area)
    result_field = result_fields.get(research_area)

    if child_graph is None or result_field is None:
        return {
            "supervisor_error": f"Unsupported research area: {research_area}"
        }

    try:
        child_output = child_graph.invoke(
            {"ticker": state["ticker"]}
        )
    except Exception as exc:
        return {
            result_field: None,
            "research_errors": {
                research_area.value: (
                    f"Child research graph invocation failed: {exc}"
                ),
            },
        }

    if not isinstance(child_output, dict):
        return {
            "supervisor_error": (
                f"Invalid output from {research_area.value} research graph: "
                "expected a dictionary."
            ),
        }

    if (
        "research_result" not in child_output
        or "research_error" not in child_output
    ):
        return {
            "supervisor_error": (
                f"Invalid output from {research_area.value} research graph: "
                "required keys 'research_result' and 'research_error' "
                "are missing."
            ),
        }

    child_result = child_output["research_result"]
    child_error = child_output["research_error"]

    if not isinstance(child_error, str):
        return {
            "supervisor_error": (
                f"Invalid output from {research_area.value} research graph: "
                "'research_error' must be a string."
            ),
        }

    child_error = child_error.strip()

    # Exactly two valid outcomes:
    # 1. Success: a non-None result and an empty error.
    # 2. Research failure: a None result and a non-empty error.
    if child_result is None and not child_error:
        return {
            "supervisor_error": (
                f"Invalid output from {research_area.value} research graph: "
                "no result was returned and no error was reported."
            ),
        }

    if child_result is not None and child_error:
        return {
            "supervisor_error": (
                f"Invalid output from {research_area.value} research graph: "
                "both a result and an error were returned."
            ),
        }

    update: dict = {
        result_field: child_result,
    }

    if child_error:
        update["research_errors"] = {
            research_area.value: child_error,
        }

    return update


def child_execution_should_continue(
    state: ResearchSupervisorState,
) -> str:
    """Stop when a child violates the output contract."""

    if state.get("supervisor_error"):
        return "error"

    return "continue"


def mark_completed(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Mark the selected research area complete, even when its child failed."""

    current = state.get("next_research_area")

    if current is None:
        return {
            "supervisor_error": "No research area is available to mark complete."
        }

    completed = list(state.get("completed_research_areas", []))

    if current not in completed:
        completed.append(current)

    return {
        "completed_research_areas": completed,
        "next_research_area": None,
        "supervisor_error": "",
    }


def supervisor_should_continue(
    state: ResearchSupervisorState,
) -> str:
    """Route to execution, finish, or stop on a planning/supervisor error."""

    if state.get("planning_error") or state.get("supervisor_error"):
        return "error"

    if state.get("next_research_area") is None:
        return "done"

    return "execute"


def prepare_valuation_outputs(
    state: ResearchSupervisorState,
) -> ResearchSupervisorState:
    """Produce the valuation input contract as part of the Research stage.

    Explicit caller overrides win. Missing values are obtained through the
    valuation provider selected in the runtime provider bundle.
    """
    ticker = state.get("ticker", "").strip().upper()
    provider = get_provider_bundle().valuation_research
    errors: list[str] = []
    updates: dict = {}

    supplied_inputs = state.get("valuation_inputs")
    if supplied_inputs is not None and not isinstance(supplied_inputs, ValuationInputs):
        updates["valuation_inputs"] = None
        errors.append("valuation_inputs override must be a ValuationInputs instance")
    elif isinstance(supplied_inputs, ValuationInputs):
        updates["valuation_inputs"] = supplied_inputs
    else:
        try:
            raw_inputs = provider.get_valuation_inputs(ticker)
            updates["valuation_inputs"] = ValuationInputs.model_validate(
                {key: value for key, value in raw_inputs.items() if key != "ticker"}
            )
        except Exception as exc:
            updates["valuation_inputs"] = None
            errors.append(f"valuation_inputs: {exc}")

    supplied_assumptions = state.get("valuation_assumptions")
    if supplied_assumptions is not None and not isinstance(
        supplied_assumptions, ValuationAssumptions
    ):
        updates["valuation_assumptions"] = None
        errors.append(
            "valuation_assumptions override must be a ValuationAssumptions instance"
        )
    elif isinstance(supplied_assumptions, ValuationAssumptions):
        updates["valuation_assumptions"] = supplied_assumptions
    else:
        try:
            raw_assumptions = provider.get_valuation_assumptions(ticker)
            updates["valuation_assumptions"] = ValuationAssumptions.model_validate(
                {key: value for key, value in raw_assumptions.items() if key != "ticker"}
            )
        except Exception as exc:
            updates["valuation_assumptions"] = None
            errors.append(f"valuation_assumptions: {exc}")

    updates["valuation_research_error"] = "; ".join(errors)
    return updates



def build_research_supervisor_graph():
    """Build the production Research-stage graph."""

    builder = StateGraph(
        ResearchSupervisorState,
        input_schema=ResearchSupervisorInputState,
        output_schema=ResearchSupervisorOutputState,
    )

    builder.add_node("plan_research", plan_research)
    builder.add_node(
        "select_next_research_area",
        select_next_research_area,
    )
    builder.add_node("route_and_execute", route_and_execute)
    builder.add_node("mark_completed", mark_completed)
    builder.add_node("prepare_valuation_outputs", prepare_valuation_outputs)

    builder.add_edge(START, "plan_research")
    builder.add_edge("plan_research", "select_next_research_area")

    builder.add_conditional_edges(
        "select_next_research_area",
        supervisor_should_continue,
        {
            "execute": "route_and_execute",
            "done": "prepare_valuation_outputs",
            "error": END,
        },
    )

    builder.add_conditional_edges(
        "route_and_execute",
        child_execution_should_continue,
        {
            "continue": "mark_completed",
            "error": END,
        },
    )

    builder.add_edge(
        "mark_completed",
        "select_next_research_area",
    )
    builder.add_edge("prepare_valuation_outputs", END)

    return builder.compile()


research_supervisor_graph = build_research_supervisor_graph()