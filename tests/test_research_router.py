from unittest.mock import MagicMock, patch

import pytest

from app.agents.models import ResearchArea, ResearchPlan
from app.agents.research_router import (
    build_research_router_graph,
    research_router_graph,
)


def make_plan(*areas):
    return ResearchPlan(
        research_areas=list(areas),
        rationale="Selected for the requested research scope.",
    )


def test_research_router_graph_is_compiled():
    assert research_router_graph is not None
    assert build_research_router_graph() is not None


@pytest.mark.parametrize(
    ("research_area", "node_name", "module_path"),
    [
        (
            ResearchArea.COMPANY,
            "company_research",
            "app.agents.research_router.company_research_graph",
        ),
        (
            ResearchArea.FINANCIAL,
            "financial_research",
            "app.agents.research_router.financial_research_graph",
        ),
        (
            ResearchArea.MARKET,
            "market_research",
            "app.agents.research_router.market_research_graph",
        ),
        (
            ResearchArea.INDUSTRY_MACRO,
            "industry_macro_research",
            "app.agents.research_router.industry_macro_research_graph",
        ),
    ],
)
def test_router_dispatches_deterministically(
    research_area,
    node_name,
    module_path,
):
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "research_result": f"{node_name} result",
        "research_error": "",
    }

    with patch(module_path, fake_graph):
        output = research_router_graph.invoke(
            {
                "ticker": "AAPL",
                "research_plan": make_plan(research_area),
                "next_research_area": research_area,
            }
        )

    assert output["routed_area"] == research_area
    assert output["research_result"] == f"{node_name} result"
    assert output["research_error"] == ""
    assert output["routing_error"] == ""
    fake_graph.invoke.assert_called_once_with({"ticker": "AAPL"})


def test_router_does_not_call_llm():
    # The router is a deterministic Python function and has no LLM call.
    plan = make_plan(ResearchArea.COMPANY)

    with patch(
        "app.agents.research_router.company_research_graph"
    ) as fake_graph:
        fake_graph.invoke.return_value = {
            "research_result": "company result",
            "research_error": "",
        }

        output = research_router_graph.invoke(
            {
                "ticker": "AAPL",
                "research_plan": plan,
                "next_research_area": ResearchArea.COMPANY,
            }
        )

    assert output["routed_area"] == ResearchArea.COMPANY


def test_router_rejects_area_not_in_plan():
    output = research_router_graph.invoke(
        {
            "ticker": "AAPL",
            "research_plan": make_plan(ResearchArea.COMPANY),
            "next_research_area": ResearchArea.FINANCIAL,
        }
    )

    assert output["routed_area"] is None
    assert output["research_result"] is None
    assert output["routing_error"] == (
        "Research area is not included in the research plan: financial"
    )


def test_router_graph_contains_all_agent_routes():
    nodes = research_router_graph.get_graph().nodes

    assert "router" in nodes
    assert "company_research" in nodes
    assert "financial_research" in nodes
    assert "market_research" in nodes
    assert "industry_macro_research" in nodes
    assert "routing_error" in nodes
