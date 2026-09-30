from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    ResearchArea,
    ResearchPlan,
)
from app.agents.research_state import ResearchState


def make_plan(*areas):
    return ResearchPlan(
        research_areas=list(areas),
        rationale="Selected for the requested research scope.",
    )


def test_shared_research_state_contains_all_agent_result_fields():
    state: ResearchState = {
        "ticker": "AAPL",
        "research_plan": make_plan(
            ResearchArea.COMPANY,
            ResearchArea.FINANCIAL,
            ResearchArea.MARKET,
            ResearchArea.INDUSTRY_MACRO,
        ),
        "next_research_area": ResearchArea.COMPANY,
        "company_research": None,
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "research_errors": {},
    }

    assert state["company_research"] is None
    assert state["financial_research"] is None
    assert state["market_research"] is None
    assert state["industry_macro_research"] is None
    assert state["research_errors"] == {}


def test_shared_state_uses_dedicated_result_fields():
    company_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Company research.",
    )
    financial_result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100.0,
        net_income=20.0,
        profit_margin=0.2,
        summary="Financial research.",
    )

    state: ResearchState = {
        "company_research": company_result,
        "financial_research": financial_result,
        "research_errors": {},
    }

    assert state["company_research"] == company_result
    assert state["financial_research"] == financial_result
    assert state["company_research"] is not state["financial_research"]


def test_shared_research_state_does_not_expose_valuation_internals():
    state: ResearchState = {
        "ticker": "AAPL",
        "company_research": None,
        "financial_research": None,
        "market_research": None,
        "industry_macro_research": None,
        "research_errors": {},
        "valuation_analysis": None,
        "valuation_error": "",
    }

    assert "valuation_inputs" not in state
    assert "valuation_assumptions" not in state
    assert "valuation_analysis" in state