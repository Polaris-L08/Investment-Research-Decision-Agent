from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.research_state import ResearchState
from app.valuation.calculations import calculate_pe_implied_value
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


class ValuationInputState(ResearchState, total=False):
    """Input boundary for the valuation graph."""

    valuation_inputs: ValuationInputs
    valuation_assumptions: ValuationAssumptions


class ValuationOutputState(ResearchState, total=False):
    """Output boundary for the valuation graph."""

    valuation_analysis: ValuationResult | None
    valuation_error: str


def valuation_agent(
    state: ResearchState,
) -> ResearchState:
    """Run the deterministic valuation model from shared research state."""

    ticker = state.get("ticker")
    inputs = state.get("valuation_inputs")
    assumptions = state.get("valuation_assumptions")

    if not ticker:
        return {
            "valuation_analysis": None,
            "valuation_error": "Ticker is required for valuation.",
        }

    if inputs is None:
        return {
            "valuation_analysis": None,
            "valuation_error": "Valuation inputs are required.",
        }

    if assumptions is None:
        return {
            "valuation_analysis": None,
            "valuation_error": "Valuation assumptions are required.",
        }

    try:
        implied_value = calculate_pe_implied_value(
            inputs,
            assumptions,
        )

        result = ValuationResult(
            ticker=ticker,
            method=ValuationMethod.PE,
            inputs=inputs,
            assumptions=assumptions,
            implied_value_per_share=implied_value,
            metadata=ValuationMetadata(
                currency="USD",
                model_version="pe-v1",
            ),
        )

    except Exception as exc:
        return {
            "valuation_analysis": None,
            "valuation_error": str(exc),
        }

    return {
        "valuation_analysis": result,
        "valuation_error": "",
    }


def build_valuation_graph():
    """Build the Phase 6 valuation graph."""

    builder = StateGraph(
        ResearchState,
        input_schema=ValuationInputState,
        output_schema=ValuationOutputState,
    )

    builder.add_node(
        "valuation_agent",
        valuation_agent,
    )

    builder.add_edge(
        START,
        "valuation_agent",
    )

    builder.add_edge(
        "valuation_agent",
        END,
    )

    return builder.compile()


valuation_graph = build_valuation_graph()