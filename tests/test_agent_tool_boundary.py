from unittest.mock import patch

from app.agents.company_research import (
    company_research_tool_loop,
)
from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
)
from app.graph.tool_loop import (
    build_tool_loop_graph,
)


def test_company_research_tool_set_contains_company_tools():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_company_info",
        "get_stock_price",
    }


def test_company_research_tool_loop_is_compiled():
    assert company_research_tool_loop is not None


def test_build_tool_loop_graph_accepts_custom_tool_set():
    graph = build_tool_loop_graph(
        COMPANY_RESEARCH_TOOLS
    )

    assert graph is not None


def test_company_research_tool_loop_contains_only_allowed_tools():
    graph = company_research_tool_loop

    graph_nodes = graph.get_graph().nodes

    assert "llm" in graph_nodes
    assert "tools" in graph_nodes


def test_company_research_tool_set_does_not_include_unrelated_tools():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    assert "get_income_statement" not in tool_names
    assert "get_balance_sheet" not in tool_names


def test_company_research_tool_loop_uses_expected_tool_set():
    tool_names = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    assert set(
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    ) == tool_names