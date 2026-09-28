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


from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
    FINANCIAL_RESEARCH_TOOLS,
)

def test_financial_research_tool_set_contains_financial_tools():
    tool_names = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_revenue",
        "get_net_income",
    }


def test_company_and_financial_tool_sets_are_separate():
    company_tools = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    financial_tools = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert company_tools.isdisjoint(
        financial_tools
    )


def test_financial_tool_set_does_not_include_company_tools():
    tool_names = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    assert "get_company_info" not in tool_names
    assert "get_stock_price" not in tool_names


from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
    FINANCIAL_RESEARCH_TOOLS,
    MARKET_RESEARCH_TOOLS,
)


def test_market_research_tool_boundary():
    tool_names = {
        tool.name
        for tool in MARKET_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_market_index",
        "get_market_return",
    }


def test_research_agent_tool_sets_are_disjoint():
    company_tools = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    financial_tools = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    market_tools = {
        tool.name
        for tool in MARKET_RESEARCH_TOOLS
    }

    assert company_tools.isdisjoint(financial_tools)
    assert company_tools.isdisjoint(market_tools)
    assert financial_tools.isdisjoint(market_tools)


from app.agents.tool_sets import (
    COMPANY_RESEARCH_TOOLS,
    FINANCIAL_RESEARCH_TOOLS,
    MARKET_RESEARCH_TOOLS,
    INDUSTRY_MACRO_RESEARCH_TOOLS,
)


def test_industry_macro_research_tool_boundary():
    tool_names = {
        tool.name
        for tool in INDUSTRY_MACRO_RESEARCH_TOOLS
    }

    assert tool_names == {
        "get_industry_info",
        "get_macro_environment",
    }


def test_all_research_agent_tool_sets_are_disjoint():
    company_tools = {
        tool.name
        for tool in COMPANY_RESEARCH_TOOLS
    }

    financial_tools = {
        tool.name
        for tool in FINANCIAL_RESEARCH_TOOLS
    }

    market_tools = {
        tool.name
        for tool in MARKET_RESEARCH_TOOLS
    }

    industry_macro_tools = {
        tool.name
        for tool in INDUSTRY_MACRO_RESEARCH_TOOLS
    }

    tool_sets = [
        company_tools,
        financial_tools,
        market_tools,
        industry_macro_tools,
    ]

    for index, current_tools in enumerate(tool_sets):
        for other_tools in tool_sets[index + 1:]:
            assert current_tools.isdisjoint(other_tools)