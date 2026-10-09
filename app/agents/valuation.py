from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.models import CompanyResearchResult
from app.agents.research_state import ResearchState
from app.valuation.calculations import (
    calculate_expected_upside,
    calculate_pe_implied_value,
    calculate_target_price,
)
from app.valuation.input_boundary import validate_valuation_input_boundary, ValuationInputError
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMetadata,
    ValuationMethod,
    ValuationResult,
)


class ValuationInputState(TypedDict):
    """Explicit input boundary for the valuation subgraph."""

    ticker: str
    company_research: CompanyResearchResult
    valuation_inputs: ValuationInputs
    valuation_assumptions: ValuationAssumptions


class ValuationGraphState(ValuationInputState, total=False):
    """Internal state used only while executing the valuation subgraph."""

    valuation_analysis: ValuationResult | None
    valuation_error: str


class ValuationOutputState(TypedDict):
    """Output boundary returned to the parent research workflow."""

    valuation_analysis: ValuationResult | None
    valuation_error: str


def valuation_agent(
    state: ValuationGraphState,
) -> ValuationOutputState:
    """Run deterministic valuation only after the explicit input boundary passes."""

    try:
        validated = validate_valuation_input_boundary(state)
    except ValuationInputError as exc:
        return {
            "valuation_analysis": None,
            "valuation_error": str(exc),
        }

    ticker = validated.ticker
    company_research = validated.company_research
    inputs = validated.valuation_inputs
    assumptions = validated.valuation_assumptions

    current_price = company_research.current_price

    try:
        implied_value = calculate_pe_implied_value(
            inputs,
            assumptions,
        )

        target_price = calculate_target_price(implied_value)
        expected_upside = calculate_expected_upside(
            target_price,
            current_price,
        )

        result = ValuationResult(
            ticker=ticker,
            method=ValuationMethod.PE,
            inputs=inputs,
            assumptions=assumptions,
            implied_value_per_share=implied_value,
            target_price=target_price,
            current_price=current_price,
            expected_upside=expected_upside,
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
    """Build the Phase 6 valuation subgraph."""

    builder = StateGraph(
        ValuationGraphState,
        input_schema=ValuationInputState,
        output_schema=ValuationOutputState,
    )

    builder.add_node(
        "valuation_agent",
        valuation_agent,
    )

    builder.add_edge(START, "valuation_agent")
    builder.add_edge("valuation_agent", END)

    return builder.compile()


valuation_graph = build_valuation_graph()
