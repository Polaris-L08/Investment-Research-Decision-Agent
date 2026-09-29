from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_supervisor import (
    research_supervisor_graph,
)


def test_supervisor_executes_all_planned_research_areas(
    monkeypatch,
):
    executed = []

    def fake_company(state):
        executed.append(ResearchArea.COMPANY)
        return {
            "company_research": "company result",
            "research_errors": {},
        }

    def fake_financial(state):
        executed.append(ResearchArea.FINANCIAL)
        return {
            "financial_research": "financial result",
            "research_errors": {},
        }

    def fake_market(state):
        executed.append(ResearchArea.MARKET)
        return {
            "market_research": "market result",
            "research_errors": {},
        }

    def fake_industry_macro(state):
        executed.append(ResearchArea.INDUSTRY_MACRO)
        return {
            "industry_macro_research": "industry result",
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_supervisor.company_research_graph.invoke",
        fake_company,
    )
    monkeypatch.setattr(
        "app.agents.research_supervisor.financial_research_graph.invoke",
        fake_financial,
    )
    monkeypatch.setattr(
        "app.agents.research_supervisor.market_research_graph.invoke",
        fake_market,
    )
    monkeypatch.setattr(
        "app.agents.research_supervisor.industry_macro_research_graph.invoke",
        fake_industry_macro,
    )

    result = research_supervisor_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": ResearchPlan(
                research_areas=[
                    ResearchArea.COMPANY,
                    ResearchArea.FINANCIAL,
                    ResearchArea.MARKET,
                ],
                rationale=(
                    "Company, financial, and market "
                    "research are required."
                ),
            ),
        }
    )

    assert executed == [
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ]

    assert result["completed_research_areas"] == [
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ]


def test_supervisor_respects_research_plan(
    monkeypatch,
):
    executed = []

    def fake_company(state):
        executed.append(ResearchArea.COMPANY)
        return {
            "company_research": "company result",
            "research_errors": {},
        }

    def fake_market(state):
        executed.append(ResearchArea.MARKET)
        return {
            "market_research": "market result",
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_supervisor.company_research_graph.invoke",
        fake_company,
    )
    monkeypatch.setattr(
        "app.agents.research_supervisor.market_research_graph.invoke",
        fake_market,
    )

    result = research_supervisor_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": ResearchPlan(
                research_areas=[
                    ResearchArea.COMPANY,
                    ResearchArea.MARKET,
                ],
                rationale=(
                    "Only company and market research "
                    "are required."
                ),
            ),
        }
    )

    assert executed == [
        ResearchArea.COMPANY,
        ResearchArea.MARKET,
    ]

    assert "financial_research" not in result
    assert "industry_macro_research" not in result


def test_supervisor_preserves_agent_results(
    monkeypatch,
):
    def fake_company(state):
        return {
            "company_research": "company result",
            "research_errors": {},
        }

    def fake_financial(state):
        return {
            "financial_research": "financial result",
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_supervisor.company_research_graph.invoke",
        fake_company,
    )
    monkeypatch.setattr(
        "app.agents.research_supervisor.financial_research_graph.invoke",
        fake_financial,
    )

    result = research_supervisor_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": ResearchPlan(
                research_areas=[
                    ResearchArea.COMPANY,
                    ResearchArea.FINANCIAL,
                ],
                rationale=(
                    "Both company and financial research "
                    "are required."
                ),
            ),
        }
    )

    assert result["company_research"] == "company result"
    assert result["financial_research"] == "financial result"