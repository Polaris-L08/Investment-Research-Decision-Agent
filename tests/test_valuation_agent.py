from app.agents.valuation import (
    build_valuation_graph,
    valuation_agent,
    valuation_graph,
)
from app.agents.research_state import ResearchState
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMethod,
)


def make_state() -> ResearchState:
    return {
        "ticker": "AAPL",
        "valuation_inputs": ValuationInputs(
            earnings_per_share=10.0,
        ),
        "valuation_assumptions": ValuationAssumptions(
            multiple=20.0,
            rationale="Use a 20x P/E multiple for this test valuation.",
        ),
        "company_research": None,
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "research_errors": {},
    }


def test_valuation_graph_is_compiled():
    assert valuation_graph is not None
    assert build_valuation_graph() is not None


def test_valuation_agent_returns_structured_valuation_result():
    result = valuation_agent(make_state())

    valuation = result["valuation_analysis"]

    assert valuation is not None
    assert valuation.ticker == "AAPL"
    assert valuation.method is ValuationMethod.PE
    assert valuation.inputs.earnings_per_share == 10.0
    assert valuation.assumptions.multiple == 20.0
    assert valuation.implied_value_per_share == 200.0
    assert result["valuation_error"] == ""


def test_valuation_agent_requires_inputs():
    state = make_state()
    state.pop("valuation_inputs")

    result = valuation_agent(state)

    assert result["valuation_analysis"] is None
    assert result["valuation_error"] == "Valuation inputs are required."


def test_valuation_agent_requires_assumptions():
    state = make_state()
    state.pop("valuation_assumptions")

    result = valuation_agent(state)

    assert result["valuation_analysis"] is None
    assert result["valuation_error"] == "Valuation assumptions are required."


def test_valuation_graph_preserves_research_state():
    state = make_state()
    state["research_errors"] = {"company": "test error"}

    result = valuation_graph.invoke(state)

    assert result["ticker"] == "AAPL"
    assert result["research_errors"] == {"company": "test error"}
    assert result["valuation_analysis"].implied_value_per_share == 200.0
    assert result["valuation_error"] == ""