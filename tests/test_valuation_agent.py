from app.agents.models import CompanyResearchResult
from app.agents.research_state import ResearchState
from app.agents.valuation import (
    build_valuation_graph,
    valuation_agent,
    valuation_graph,
)
from app.valuation.models import (
    ValuationAssumptions,
    ValuationInputs,
    ValuationMethod,
)


def make_company_research(current_price: float = 160.0) -> CompanyResearchResult:
    return CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=current_price,
        summary="Test company research result.",
    )


def make_valuation_inputs() -> ValuationInputs:
    return ValuationInputs(earnings_per_share=10.0)


def make_valuation_assumptions() -> ValuationAssumptions:
    return ValuationAssumptions(
        multiple=20.0,
        rationale="Use a 20x P/E multiple for this test valuation.",
    )


def make_input_state() -> dict:
    return {
        "ticker": "AAPL",
        "company_research": make_company_research(),
        "valuation_inputs": make_valuation_inputs(),
        "valuation_assumptions": make_valuation_assumptions(),
    }


def test_valuation_graph_is_compiled():
    assert valuation_graph is not None
    assert build_valuation_graph() is not None


def test_valuation_agent_returns_target_price_and_expected_upside():
    result = valuation_agent(make_input_state())

    valuation = result["valuation_analysis"]

    assert valuation is not None
    assert valuation.ticker == "AAPL"
    assert valuation.method is ValuationMethod.PE
    assert valuation.inputs.earnings_per_share == 10.0
    assert valuation.assumptions.multiple == 20.0
    assert valuation.implied_value_per_share == 200.0
    assert valuation.target_price == 200.0
    assert valuation.current_price == 160.0
    assert valuation.expected_upside == 0.25
    assert result["valuation_error"] == ""


def test_valuation_graph_returns_only_valuation_output():
    result = valuation_graph.invoke(make_input_state())

    assert set(result) == {
        "valuation_analysis",
        "valuation_error",
    }
    assert result["valuation_analysis"].target_price == 200.0


def test_valuation_state_is_not_polluted_with_valuation_inputs():
    state: ResearchState = {
        "ticker": "AAPL",
        "company_research": make_company_research(),
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "research_errors": {},
        "valuation_analysis": None,
        "valuation_error": "",
    }

    assert "valuation_inputs" not in state
    assert "valuation_assumptions" not in state


def test_valuation_analysis_contains_its_input_snapshot():
    result = valuation_agent(make_input_state())
    valuation = result["valuation_analysis"]

    assert valuation.inputs == make_valuation_inputs()
    assert valuation.assumptions == make_valuation_assumptions()
    assert valuation.current_price == make_company_research().current_price
