"""Focused tests for evidence-backed fallbacks in all four research subgraphs."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from app.agents.company_research import (
    build_company_research_fallback,
    company_research_agent,
)
from app.agents.financial_research import (
    build_financial_research_fallback,
    financial_research_agent,
)
from app.agents.industry_macro_research import (
    build_industry_macro_research_fallback,
    industry_macro_research_agent,
)
from app.agents.market_research import (
    build_market_research_fallback,
    market_research_agent,
)


def _tool_result(payloads: dict[str, object], ticker: str = "AAPL") -> dict:
    calls = [
        {
            "name": name,
            "args": {"ticker": ticker},
            "id": f"call_{name}",
            "type": "tool_call",
        }
        for name in payloads
    ]
    messages = [AIMessage(content="", tool_calls=calls)]
    for name, payload in payloads.items():
        import json

        messages.append(
            ToolMessage(
                content=json.dumps(payload),
                tool_call_id=f"call_{name}",
            )
        )
    return {"messages": messages}


@pytest.mark.parametrize(
    "builder,payloads,expected_fields",
    [
        (
            build_company_research_fallback,
            {
                "get_company_info": {
                    "ticker": "AAPL", "company_name": "Apple Inc.", "sector": "Technology"
                },
                "get_stock_price": {"ticker": "AAPL", "price": 200.0},
            },
            {"company_name": "Apple Inc.", "current_price": 200.0},
        ),
        (
            build_financial_research_fallback,
            {"get_revenue": 100.0, "get_net_income": 20.0},
            {"revenue": 100.0, "net_income": 20.0, "profit_margin": 0.2},
        ),
        (
            build_market_research_fallback,
            {"get_market_index": "S&P 500", "get_market_return": 8.5},
            {"market_index": "S&P 500", "market_return": 8.5},
        ),
        (
            build_industry_macro_research_fallback,
            {
                "get_industry_info": {
                    "ticker": "AAPL", "industry": "Consumer Electronics", "industry_growth": 6.2
                },
                "get_macro_environment": {
                    "ticker": "AAPL", "macro_environment": "Expansion", "macro_growth": 2.8
                },
            },
            {"industry": "Consumer Electronics", "industry_growth": 6.2,
             "macro_environment": "Expansion", "macro_growth": 2.8},
        ),
    ],
)
def test_each_research_fallback_uses_evidence_and_marks_degraded(
    builder, payloads, expected_fields
):
    result = builder(_tool_result(payloads), ticker="AAPL")
    assert result.data_status == "degraded"
    assert result.degradation_reason
    assert "DEGRADED FALLBACK" in result.summary
    for field, expected in expected_fields.items():
        assert getattr(result, field) == expected


def test_financial_fallback_rejects_missing_core_data():
    tool_result = _tool_result({"get_revenue": 100.0})
    with pytest.raises(ValueError, match="revenue and net-income"):
        build_financial_research_fallback(tool_result, ticker="AAPL")


def test_company_fallback_rejects_mismatched_ticker():
    tool_result = _tool_result(
        {
            "get_company_info": {
                "ticker": "MSFT", "company_name": "Microsoft", "sector": "Technology"
            },
            "get_stock_price": {"ticker": "MSFT", "price": 400.0},
        }
    )
    with pytest.raises(ValueError, match="requested ticker"):
        build_company_research_fallback(tool_result, ticker="AAPL")


@pytest.mark.parametrize(
    "module,agent_name,loop_name,llm_name,builder,payloads",
    [
        (
            "app.agents.company_research", company_research_agent,
            "company_research_tool_loop", "structured_company_research_llm",
            build_company_research_fallback,
            {"get_company_info": {"ticker": "AAPL", "company_name": "Apple", "sector": "Technology"},
             "get_stock_price": {"ticker": "AAPL", "price": 200.0}},
        ),
        (
            "app.agents.financial_research", financial_research_agent,
            "financial_research_tool_loop", "structured_financial_research_llm",
            build_financial_research_fallback,
            {"get_revenue": 100.0, "get_net_income": 20.0},
        ),
        (
            "app.agents.market_research", market_research_agent,
            "market_research_tool_loop", "structured_market_research_llm",
            build_market_research_fallback,
            {"get_market_index": "S&P 500", "get_market_return": 8.5},
        ),
        (
            "app.agents.industry_macro_research", industry_macro_research_agent,
            "industry_macro_research_tool_loop", "structured_industry_macro_research_llm",
            build_industry_macro_research_fallback,
            {"get_industry_info": {"ticker": "AAPL", "industry": "Technology", "industry_growth": 6.2},
             "get_macro_environment": {"ticker": "AAPL", "macro_environment": "Expansion", "macro_growth": 2.8}},
        ),
    ],
)
def test_each_agent_enters_fallback_only_after_synthesis_failure(
    module, agent_name, loop_name, llm_name, builder, payloads
):
    from importlib import import_module

    imported = import_module(module)
    fake_loop = MagicMock()
    fake_loop.invoke.return_value = _tool_result(payloads)
    fake_llm = MagicMock()
    fake_llm.invoke.side_effect = RuntimeError("structured output unavailable")

    with patch.object(imported, loop_name, fake_loop), patch.object(imported, llm_name, fake_llm):
        result = agent_name({"ticker": "AAPL", "research_result": None, "research_error": ""})

    assert result["research_error"] == ""
    assert result["research_result"].data_status == "degraded"
    assert result["research_result"].degradation_reason
    fake_loop.invoke.assert_called_once()
    fake_llm.invoke.assert_called_once()


def test_tool_loop_failure_is_not_converted_into_fallback_success():
    fake_loop = MagicMock()
    fake_loop.invoke.side_effect = RuntimeError("provider unavailable")
    with patch("app.agents.market_research.market_research_tool_loop", fake_loop):
        result = market_research_agent(
            {"ticker": "AAPL", "research_result": None, "research_error": ""}
        )
    assert result["research_result"] is None
    assert result["research_error"] == "provider unavailable"


def test_synthesis_timeout_does_not_enter_fallback():
    fake_loop = MagicMock()
    fake_loop.invoke.return_value = _tool_result(
        {"get_market_index": "S&P 500", "get_market_return": 8.5}
    )
    fake_llm = MagicMock()
    fake_llm.invoke.side_effect = TimeoutError("structured synthesis timeout")

    with patch("app.agents.market_research.market_research_tool_loop", fake_loop), patch(
        "app.agents.market_research.structured_market_research_llm", fake_llm
    ):
        result = market_research_agent(
            {"ticker": "AAPL", "research_result": None, "research_error": ""}
        )

    assert result["research_result"] is None
    assert "timeout" in result["research_error"].lower()
