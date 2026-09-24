from langchain_core.messages import HumanMessage

from app.graph.tool_loop import build_tool_loop_graph


def test_stock_price_end_to_end():
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

    assert messages[0].type == "human"

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    tool_message = tool_messages[0]

    assert "AAPL" in tool_message.content
    assert "200.0" in tool_message.content

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls


def test_company_info_end_to_end():
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

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    tool_message = tool_messages[0]

    assert "Apple Inc." in tool_message.content
    assert "Technology" in tool_message.content

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls


def test_multiple_tools_end_to_end():
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
        if message.type != "ai":
            continue

        for tool_call in message.tool_calls:
            tool_names.append(tool_call["name"])

    assert "get_stock_price" in tool_names
    assert "get_company_info" in tool_names

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert tool_messages

    final_message = messages[-1]

    assert final_message.type == "ai"
    assert not final_message.tool_calls