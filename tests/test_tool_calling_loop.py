from langchain_core.messages import HumanMessage

from app.graph.tool_loop import build_tool_loop_graph


def test_tool_calling_loop_returns_final_answer():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price "
                        "of AAPL?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    assert len(messages) >= 4

    assert messages[0].type == "human"
    assert messages[1].type == "ai"
    assert messages[1].tool_calls

    assert messages[2].type == "tool"
    assert messages[3].type == "ai"

    assert not messages[3].tool_calls


def test_tool_calling_loop_can_use_company_info():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What company is AAPL and "
                        "what sector does it belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_calls = [
        message.tool_calls
        for message in messages
        if message.type == "ai"
        and message.tool_calls
    ]

    assert tool_calls

    first_tool_call = tool_calls[0][0]

    assert first_tool_call["name"] == "get_company_info"
    assert first_tool_call["args"]["ticker"] == "AAPL"

    assert messages[-1].type == "ai"
    assert not messages[-1].tool_calls


def test_tool_calling_loop_can_use_multiple_tools():
    graph = build_tool_loop_graph()

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "What is the current stock price of AAPL, "
                        "and what sector does the company belong to?"
                    )
                )
            ]
        }
    )

    messages = result["messages"]

    tool_names = []

    for message in messages:
        if message.type == "ai":
            for tool_call in message.tool_calls:
                tool_names.append(tool_call["name"])

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    assert messages[-1].type == "ai"
    assert not messages[-1].tool_calls