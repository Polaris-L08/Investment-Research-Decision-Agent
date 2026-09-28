from unittest.mock import MagicMock, patch

from app.agents.industry_macro_research import (
    industry_macro_research_graph,
)
from app.agents.models import IndustryMacroResearchResult


def test_industry_macro_research_graph_returns_expected_result():
    result = IndustryMacroResearchResult(
        ticker="AAPL",
        industry="Consumer Electronics",
        industry_growth=6.2,
        macro_environment="Expansion",
        macro_growth=2.8,
        summary=(
            "The company operates in a growing consumer "
            "electronics industry within an expansionary "
            "macro environment."
        ),
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = {
        "messages": []
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.industry_macro_research."
        "structured_industry_macro_research_llm",
        fake_structured_llm,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"] == result
    assert output["research_error"] == ""


def test_industry_macro_research_graph_maps_agent_failure():
    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.side_effect = RuntimeError(
        "Industry macro tool loop failed."
    )

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"] is None
    assert output["research_error"] == (
        "Industry macro tool loop failed."
    )


def test_industry_macro_research_agent_only_requires_ticker():
    result = IndustryMacroResearchResult(
        ticker="AAPL",
        industry="Consumer Electronics",
        industry_growth=6.2,
        macro_environment="Expansion",
        macro_growth=2.8,
        summary="Industry and macro conditions were positive.",
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = {
        "messages": []
    }

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = result

    with patch(
        "app.agents.industry_macro_research."
        "industry_macro_research_tool_loop",
        fake_tool_loop,
    ), patch(
        "app.agents.industry_macro_research."
        "structured_industry_macro_research_llm",
        fake_structured_llm,
    ):
        output = industry_macro_research_graph.invoke(
            {"ticker": "AAPL"}
        )

    assert output["research_result"].ticker == "AAPL"