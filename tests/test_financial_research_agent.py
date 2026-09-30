from unittest.mock import MagicMock, patch

from app.agents.financial_research import (
    financial_research_graph,
    build_financial_research_graph,
    financial_research_tool_loop,
)
from app.agents.models import FinancialResearchResult


def test_financial_research_result_model():
    result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100000.0,
        net_income=25000.0,
        profit_margin=0.25,
        summary="Apple generated strong net income.",
    )

    assert result.ticker == "AAPL"
    assert result.revenue == 100000.0
    assert result.net_income == 25000.0
    assert result.profit_margin == 0.25


def test_financial_research_graph_is_compiled():
    assert financial_research_graph is not None


def test_build_financial_research_graph():
    graph = build_financial_research_graph()

    assert graph is not None


def test_financial_research_agent_uses_financial_tool_loop():
    assert financial_research_tool_loop is not None


def test_financial_research_agent_maps_tool_result():
    fake_result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100000.0,
        net_income=25000.0,
        profit_margin=0.25,
        summary="Apple generated strong net income.",
    )

    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.return_value = {
        "messages": [],
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_result

    with patch(
        "app.agents.financial_research.financial_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.financial_research.structured_financial_research_llm",
        fake_structured_llm,
    ):

        result = financial_research_graph.invoke(
            {
                "ticker": "AAPL",
            }
        )

    assert result["research_result"] == fake_result
    assert result["research_error"] == ""

    fake_tool_loop.invoke.assert_called_once()


def test_financial_research_agent_calculates_profit_margin_deterministically():
    llm_result = FinancialResearchResult(
        ticker="AAPL",
        revenue=100000.0,
        net_income=25000.0,
        profit_margin=999.0,
        summary="Financial research.",
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = {"messages": []}

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = llm_result

    with patch(
        "app.agents.financial_research.financial_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.financial_research.structured_financial_research_llm",
        fake_structured_llm,
    ):
        result = financial_research_graph.invoke({"ticker": "AAPL"})

    assert result["research_result"].profit_margin == 0.25