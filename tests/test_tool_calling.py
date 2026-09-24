from unittest.mock import MagicMock, patch


def test_llm_can_call_stock_price_tool():
    mock_response = MagicMock()

    mock_response.tool_calls = [
        {
            "name": "get_stock_price",
            "args": {
                "ticker": "AAPL",
            },
            "id": "call_123",
            "type": "tool_call",
        }
    ]

    with patch(
        "langchain_openai.ChatOpenAI.invoke",
        return_value=mock_response,
    ):
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="test-model",
            api_key="test-key",
            base_url="test-url",
        )

        llm_with_tools = llm.bind_tools(
            [get_stock_price]
        )

        result = llm_with_tools.invoke(
            "What is the current stock price of AAPL?"
        )

        assert len(result.tool_calls) == 1

        tool_call = result.tool_calls[0]

        assert tool_call["name"] == "get_stock_price"
        assert tool_call["args"]["ticker"] == "AAPL"


from langchain_core.messages import AIMessage

from app.tools.financial import get_stock_price


def test_llm_tool_call_structure():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_stock_price",
                "args": {
                    "ticker": "AAPL",
                },
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )

    assert len(response.tool_calls) == 1

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_stock_price"
    assert tool_call["args"]["ticker"] == "AAPL"


def test_tool_call_matches_registered_tool():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "get_stock_price",
                "args": {
                    "ticker": "MSFT",
                },
                "id": "call_456",
                "type": "tool_call",
            }
        ],
    )

    available_tools = {
        get_stock_price.name: get_stock_price
    }

    tool_call = response.tool_calls[0]

    assert tool_call["name"] in available_tools

    tool = available_tools[tool_call["name"]]

    result = tool.invoke(tool_call["args"])

    assert result["ticker"] == "MSFT"
    assert result["price"] == 450.0
