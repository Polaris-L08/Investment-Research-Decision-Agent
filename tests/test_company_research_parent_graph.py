from unittest.mock import MagicMock, patch

from app.agents.models import CompanyResearchResult
from app.graph.graph import (
    company_research_node,
    graph,
    route_after_company_research,
)


def test_company_research_node_maps_agent_result_to_parent_state():
    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple is a technology company.",
    )

    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": fake_result,
        "research_error": "",
    }

    state = {
        "ticker": "AAPL",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = company_research_node(state)

    fake_company_research_graph.invoke.assert_called_once_with(
        {
            "ticker": "AAPL",
        }
    )

    assert result["company_research_result"] == fake_result

    assert result["current_price"] == 200.0

    assert result["failure_reason"] == ""


def test_company_research_node_maps_agent_failure():
    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": None,
        "research_error": "Tool execution failed",
    }

    state = {
        "ticker": "AAPL",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = company_research_node(state)

    assert result["company_research_result"] is None

    assert result["current_price"] is None

    assert result["failure_reason"] == (
        "Company research failed: Tool execution failed"
    )


def test_company_research_node_only_passes_required_input_state():
    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple is a technology company.",
    )

    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": fake_result,
        "research_error": "",
    }

    state = {
        "ticker": "AAPL",
        "user_query": "Analyze Apple",
        "research_plan": [],
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        company_research_node(state)

    fake_company_research_graph.invoke.assert_called_once_with(
        {
            "ticker": "AAPL",
        }
    )


def test_company_research_route_continues_on_success():
    state = {
        "failure_reason": "",
    }

    assert route_after_company_research(state) == "continue"


def test_company_research_route_goes_to_failure_on_error():
    state = {
        "failure_reason": (
            "Company research failed: Tool execution failed"
        ),
    }

    assert route_after_company_research(state) == "failure"


def test_parent_graph_contains_company_research_node():
    node_names = set(
        graph.get_graph().nodes.keys()
    )

    assert "company_research" in node_names

    assert "company_research_failure" in node_names


def test_parent_graph_routes_company_research_failure_to_failure_output():
    fake_company_research_graph = MagicMock()

    fake_company_research_graph.invoke.return_value = {
        "research_result": None,
        "research_error": "Provider unavailable",
    }

    with patch(
        "app.graph.graph.company_research_graph",
        fake_company_research_graph,
    ):
        result = graph.invoke(
            {
                "user_query": "Analyze Apple",
                "ticker": "AAPL",
            }
        )

    assert result["ticker"] == "AAPL"

    assert result["failure_reason"] == (
        "Company research failed: Provider unavailable"
    )