from unittest.mock import MagicMock, patch

from app.agents.market_research import (
    market_research_graph,
)
from app.agents.models import MarketResearchResult


def test_market_research_graph_returns_expected_result():
    result = MarketResearchResult(
        ticker="AAPL",
        market_index="S&P 500",
        market_return=8.5,
        summary="The relevant market environment has been positive.",
    )

    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.return_value = {
        "messages": [],
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.market_research.market_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.market_research.structured_market_research_llm",
        fake_structured_llm,
    ):
        output = market_research_graph.invoke(
            {
                "ticker": "AAPL",
            }
        )

    assert output["research_result"] == result
    assert output["research_error"] == ""


def test_market_research_graph_maps_agent_failure():
    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.side_effect = RuntimeError(
        "Market tool loop failed."
    )

    with patch(
        "app.agents.market_research.market_research_tool_loop",
        fake_tool_loop,
    ):
        output = market_research_graph.invoke(
            {
                "ticker": "AAPL",
            }
        )

    assert output["research_result"] is None
    assert output["research_error"] == "Market tool loop failed."


def test_market_research_agent_only_requires_ticker():
    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.return_value = {
        "messages": [],
    }

    fake_result = MarketResearchResult(
        ticker="AAPL",
        market_index="S&P 500",
        market_return=8.5,
        summary="Market conditions were positive.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_result

    with patch(
        "app.agents.market_research.market_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.market_research.structured_market_research_llm",
        fake_structured_llm,
    ):
        output = market_research_graph.invoke(
            {
                "ticker": "AAPL",
            }
        )

    assert output["research_result"].ticker == "AAPL"