from unittest.mock import MagicMock, patch

from app.agents.models import (
    CompanyResearchResult,
    FinancialResearchResult,
    IndustryMacroResearchResult,
    MarketResearchResult,
    ResearchArea,
    ResearchPlan,
)
from app.agents.research_orchestrator import (
    RESEARCH_ORDER,
    build_research_orchestrator_graph,
    research_orchestrator_graph,
)


def make_plan(*areas):
    return ResearchPlan(
        research_areas=list(areas),
        rationale="Selected for the requested research scope.",
    )


def test_research_orchestrator_graph_is_compiled():
    assert research_orchestrator_graph is not None
    assert build_research_orchestrator_graph() is not None


def test_research_order_is_deterministic():
    assert RESEARCH_ORDER == [
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
        ResearchArea.INDUSTRY_MACRO,
    ]


def test_orchestrator_executes_selected_agents_sequentially():
    plan = make_plan(
        ResearchArea.COMPANY,
        ResearchArea.MARKET,
        ResearchArea.INDUSTRY_MACRO,
    )

    fake_planner = MagicMock()
    fake_planner.invoke.return_value = {
        "research_plan": plan,
        "planning_error": "",
    }

    execution_order = []

    def fake_router_invoke(state):
        area = state["next_research_area"]
        execution_order.append(area)

        results = {
            ResearchArea.COMPANY: {
                "routed_area": ResearchArea.COMPANY,
                "company_research": CompanyResearchResult(
                    ticker="AAPL",
                    company_name="Apple",
                    sector="Technology",
                    current_price=200.0,
                    summary="Company result",
                ),
                "research_errors": {},
                "routing_error": "",
            },
            ResearchArea.MARKET: {
                "routed_area": ResearchArea.MARKET,
                "market_research": MarketResearchResult(
                    ticker="AAPL",
                    market_index="S&P 500",
                    market_return=0.1,
                    summary="Market result",
                ),
                "research_errors": {},
                "routing_error": "",
            },
            ResearchArea.INDUSTRY_MACRO: {
                "routed_area": ResearchArea.INDUSTRY_MACRO,
                "industry_macro_research": IndustryMacroResearchResult(
                    ticker="AAPL",
                    industry="Technology",
                    industry_growth=0.08,
                    macro_environment="Stable",
                    macro_growth=0.02,
                    summary="Industry result",
                ),
                "research_errors": {},
                "routing_error": "",
            },
        }
        return results[area]

    fake_router = MagicMock()
    fake_router.invoke.side_effect = fake_router_invoke

    with patch(
        "app.agents.research_orchestrator.research_planner_graph",
        fake_planner,
    ), patch(
        "app.agents.research_orchestrator.research_router_graph",
        fake_router,
    ):
        output = research_orchestrator_graph.invoke(
            {
                "user_query": "Research AAPL.",
                "ticker": "AAPL",
            }
        )

    assert execution_order == [
        ResearchArea.COMPANY,
        ResearchArea.MARKET,
        ResearchArea.INDUSTRY_MACRO,
    ]
    assert output["company_research"].ticker == "AAPL"
    assert output["market_research"].ticker == "AAPL"
    assert output["industry_macro_research"].ticker == "AAPL"
    assert fake_router.invoke.call_count == 3


def test_orchestrator_skips_unselected_agents():
    plan = make_plan(ResearchArea.FINANCIAL)

    fake_planner = MagicMock()
    fake_planner.invoke.return_value = {
        "research_plan": plan,
        "planning_error": "",
    }

    fake_router = MagicMock()
    fake_router.invoke.return_value = {
        "routed_area": ResearchArea.FINANCIAL,
        "financial_research": FinancialResearchResult(
            ticker="AAPL",
            revenue=100.0,
            net_income=20.0,
            profit_margin=0.2,
            summary="Financial result",
        ),
        "research_errors": {},
        "routing_error": "",
    }

    with patch(
        "app.agents.research_orchestrator.research_planner_graph",
        fake_planner,
    ), patch(
        "app.agents.research_orchestrator.research_router_graph",
        fake_router,
    ):
        output = research_orchestrator_graph.invoke(
            {
                "user_query": "Research AAPL financials.",
                "ticker": "AAPL",
            }
        )

    assert output["financial_research"].ticker == "AAPL"
    assert "company_research" not in output or output["company_research"] is None
    assert "market_research" not in output or output["market_research"] is None
    assert fake_router.invoke.call_count == 1
    assert fake_router.invoke.call_args.args[0]["next_research_area"] == ResearchArea.FINANCIAL


def test_orchestrator_stops_when_planner_fails():
    fake_planner = MagicMock()
    fake_planner.invoke.return_value = {
        "research_plan": None,
        "planning_error": "Planner failed.",
    }

    fake_router = MagicMock()

    with patch(
        "app.agents.research_orchestrator.research_planner_graph",
        fake_planner,
    ), patch(
        "app.agents.research_orchestrator.research_router_graph",
        fake_router,
    ):
        output = research_orchestrator_graph.invoke(
            {
                "user_query": "Research AAPL.",
                "ticker": "AAPL",
            }
        )

    assert output["planning_error"] == "Planner failed."
    assert output["orchestration_error"] == "Planner failed."
    fake_router.invoke.assert_not_called()


def test_orchestrator_stops_on_routing_error():
    plan = make_plan(ResearchArea.COMPANY, ResearchArea.FINANCIAL)

    fake_planner = MagicMock()
    fake_planner.invoke.return_value = {
        "research_plan": plan,
        "planning_error": "",
    }

    fake_router = MagicMock()
    fake_router.invoke.return_value = {
        "routed_area": None,
        "routing_error": "invalid route",
        "research_errors": {},
    }

    with patch(
        "app.agents.research_orchestrator.research_planner_graph",
        fake_planner,
    ), patch(
        "app.agents.research_orchestrator.research_router_graph",
        fake_router,
    ):
        output = research_orchestrator_graph.invoke(
            {
                "user_query": "Research AAPL.",
                "ticker": "AAPL",
            }
        )

    assert output["routing_error"] == "invalid route"
    assert output["orchestration_error"] == "invalid route"
    assert fake_router.invoke.call_count == 1


def test_orchestrator_exposes_routed_area(
    monkeypatch,
):
    """Orchestrator should preserve the routed research area."""
    plan = ResearchPlan(
        research_areas=[ResearchArea.COMPANY],
        rationale="Company research is required.",
    )

    monkeypatch.setattr(
        "app.agents.research_orchestrator.research_planner_graph.invoke",
        lambda state: {
            "research_plan": plan,
            "planning_error": "",
        },
    )

    monkeypatch.setattr(
        "app.agents.research_orchestrator.research_router_graph.invoke",
        lambda state: {
            "routed_area": ResearchArea.COMPANY,
            "routing_error": "",
            "company_research": None,
            "financial_research": None,
            "market_research": None,
            "industry_macro_research": None,
            "research_errors": {},
        },
    )

    result = research_orchestrator_graph.invoke(
        {
            "user_query": "Analyze Apple.",
            "ticker": "AAPL",
        }
    )

    assert result["routed_area"] == ResearchArea.COMPANY


def test_orchestrator_executes_multiple_research_areas_sequentially(
    monkeypatch,
):
    """Orchestrator should execute multiple selected areas in order."""
    plan = ResearchPlan(
        research_areas=[
            ResearchArea.COMPANY,
            ResearchArea.FINANCIAL,
            ResearchArea.MARKET,
        ],
        rationale=(
            "Company, financial, and market research are "
            "required."
        ),
    )

    executed_areas = []

    monkeypatch.setattr(
        "app.agents.research_orchestrator.research_planner_graph.invoke",
        lambda state: {
            "research_plan": plan,
            "planning_error": "",
        },
    )

    def mock_router(state):
        research_area = state["next_research_area"]
        executed_areas.append(research_area)

        return {
            "routed_area": research_area,
            "routing_error": "",
            "company_research": None,
            "financial_research": None,
            "market_research": None,
            "industry_macro_research": None,
            "research_errors": {},
        }

    monkeypatch.setattr(
        "app.agents.research_orchestrator.research_router_graph.invoke",
        mock_router,
    )

    result = research_orchestrator_graph.invoke(
        {
            "user_query": "Analyze Apple.",
            "ticker": "AAPL",
        }
    )

    assert executed_areas == [
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ]

    assert result["completed_research_areas"] == [
        ResearchArea.COMPANY,
        ResearchArea.FINANCIAL,
        ResearchArea.MARKET,
    ]