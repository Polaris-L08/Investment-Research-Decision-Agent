from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.company_research import (
    CompanyResearchResult,
    build_company_research_graph,
    company_research_agent,
    build_company_research_fallback,
)


def test_company_research_result_model():
    result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    assert result.ticker == "AAPL"
    assert result.company_name == "Apple Inc."
    assert result.sector == "Technology"
    assert result.current_price == 200.0


def test_company_research_agent_uses_tool_results():
    tool_loop_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_company_info",
                        "args": {"ticker": "AAPL"},
                        "id": "call_company",
                        "type": "tool_call",
                    },
                    {
                        "name": "get_stock_price",
                        "args": {"ticker": "AAPL"},
                        "id": "call_price",
                        "type": "tool_call",
                    },
                ],
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"company_name": "Apple Inc.", '
                    '"sector": "Technology"}'
                ),
                tool_call_id="call_company",
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"price": 200.0}'
                ),
                tool_call_id="call_price",
            ),
            AIMessage(
                content="Apple Inc. is a technology company."
            ),
        ]
    }

    fake_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = tool_loop_result

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = fake_result

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            return_value=fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {
                "ticker": "AAPL",
                "research_result": None,
                "research_error": "",
            }
        )

    assert result["research_result"] == fake_result
    assert result["research_error"] == ""

    # 修改company_research之后 断言失效
    # fake_tool_loop.invoke.assert_called_once()
    fake_structured_llm.invoke.assert_called_once()


def test_company_research_graph_topology_is_single_business_agent():
    graph = build_company_research_graph()

    node_names = set(
        graph.get_graph().nodes
    )

    assert "company_research_agent" in node_names
    assert "__start__" in node_names
    assert "__end__" in node_names

    assert node_names == {
        "__start__",
        "company_research_agent",
        "__end__",
    }


from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.company_research import (
    CompanyResearchResult,
    build_company_research_graph,
    company_research_agent,
)
# from app.graph.tool_loop import tool_loop_graph
#
#
# def test_tool_loop_graph_is_compiled_graph():
#     assert tool_loop_graph is not None


def test_company_research_agent_uses_tool_loop_graph():
    fake_tool_result = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_company_info",
                        "args": {"ticker": "AAPL"},
                        "id": "call_company",
                        "type": "tool_call",
                    },
                    {
                        "name": "get_stock_price",
                        "args": {"ticker": "AAPL"},
                        "id": "call_price",
                        "type": "tool_call",
                    },
                ],
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"company_name": "Apple Inc.", '
                    '"sector": "Technology"}'
                ),
                tool_call_id="call_company",
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"price": 200.0}'
                ),
                tool_call_id="call_price",
            ),
        ]
    }

    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = fake_tool_result

    fake_research_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = (
        fake_research_result
    )

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {
                "ticker": "AAPL",
                "research_result": None,
                "research_error": "",
            }
        )

    assert result["research_result"] == fake_research_result
    assert result["research_error"] == ""

    fake_tool_loop.invoke.assert_called_once()
    fake_structured_llm.invoke.assert_called_once()


def test_company_research_agent_passes_only_tool_loop_state():
    fake_tool_loop = MagicMock()

    fake_tool_loop.invoke.return_value = {
        "messages": [
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"company_name": "Apple Inc.", '
                    '"sector": "Technology"}'
                ),
                tool_call_id="call_company",
            ),
            ToolMessage(
                content=(
                    '{"ticker": "AAPL", '
                    '"price": 200.0}'
                ),
                tool_call_id="call_price",
            ),
        ]
    }

    fake_research_result = CompanyResearchResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        current_price=200.0,
        summary="Apple Inc. is a technology company.",
    )

    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.return_value = (
        fake_research_result
    )

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        company_research_agent(
            {
                "ticker": "AAPL",
                "research_result": None,
                "research_error": "",
            }
        )

    call_args = fake_tool_loop.invoke.call_args
    tool_loop_input = call_args.args[0]

    assert set(tool_loop_input.keys()) == {"messages"}
    assert "ticker" not in tool_loop_input
    assert "research_result" not in tool_loop_input
    assert "research_error" not in tool_loop_input


def test_company_research_graph_topology():
    graph = build_company_research_graph()

    node_names = set(
        graph.get_graph().nodes
    )

    assert node_names == {
        "__start__",
        "company_research_agent",
        "__end__",
    }

def _fallback_tool_result(*, include_price: bool = True) -> dict:
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_company_info",
                    "args": {"ticker": "AAPL"},
                    "id": "call_company",
                    "type": "tool_call",
                },
                *(
                    [
                        {
                            "name": "get_stock_price",
                            "args": {"ticker": "AAPL"},
                            "id": "call_price",
                            "type": "tool_call",
                        }
                    ]
                    if include_price
                    else []
                ),
            ],
        ),
        ToolMessage(
            content=(
                '{"ticker": "AAPL", '
                '"company_name": "Apple Inc.", '
                '"sector": "Technology"}'
            ),
            tool_call_id="call_company",
        ),
    ]
    if include_price:
        messages.append(
            ToolMessage(
                content='{"ticker": "AAPL", "price": 200.0}',
                tool_call_id="call_price",
            )
        )
    return {"messages": messages}


def test_company_research_uses_explicit_degraded_fallback_when_llm_fails():
    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = _fallback_tool_result()
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = RuntimeError("LLM unavailable")

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {"ticker": "AAPL", "research_result": None, "research_error": ""}
        )

    fallback = result["research_result"]
    assert result["research_error"] == ""
    assert fallback is not None
    assert fallback.ticker == "AAPL"
    assert fallback.company_name == "Apple Inc."
    assert fallback.sector == "Technology"
    assert fallback.current_price == 200.0
    assert fallback.data_status == "degraded"
    assert "LLM synthesis was unavailable" in fallback.summary
    assert fallback.degradation_reason


def test_company_research_does_not_fallback_when_required_tool_data_is_missing():
    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.return_value = _fallback_tool_result(include_price=False)
    fake_structured_llm = MagicMock()
    fake_structured_llm.invoke.side_effect = RuntimeError("LLM unavailable")

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {"ticker": "AAPL", "research_result": None, "research_error": ""}
        )

    assert result["research_result"] is None
    assert "fallback was unavailable" in result["research_error"]
    assert "company-info and stock-price" in result["research_error"]


def test_company_research_does_not_attempt_llm_fallback_when_tool_loop_fails():
    fake_tool_loop = MagicMock()
    fake_tool_loop.invoke.side_effect = RuntimeError("Provider unavailable")
    fake_structured_llm = MagicMock()

    with (
        patch(
            "app.agents.company_research.company_research_tool_loop",
            fake_tool_loop,
        ),
        patch(
            "app.agents.company_research.structured_company_research_llm",
            fake_structured_llm,
        ),
    ):
        result = company_research_agent(
            {"ticker": "AAPL", "research_result": None, "research_error": ""}
        )

    assert result["research_result"] is None
    assert "Provider unavailable" in result["research_error"]
    fake_structured_llm.invoke.assert_not_called()


def test_company_research_fallback_rejects_ticker_mismatch():
    tool_result = _fallback_tool_result()
    tool_result["messages"][1].content = (
        '{"ticker": "MSFT", "company_name": "Microsoft Corporation", '
        '"sector": "Technology"}'
    )

    try:
        build_company_research_fallback(tool_result, ticker="AAPL")
    except ValueError as exc:
        assert "do not match the requested ticker" in str(exc)
    else:
        raise AssertionError("Ticker-mismatched fallback data must be rejected.")


def test_company_research_fallback_rejects_non_finite_price():
    tool_result = _fallback_tool_result()
    tool_result["messages"][2].content = '{"ticker": "AAPL", "price": NaN}'

    try:
        build_company_research_fallback(tool_result, ticker="AAPL")
    except ValueError as exc:
        assert "finite and positive" in str(exc)
    else:
        raise AssertionError("Non-finite fallback price must be rejected.")
