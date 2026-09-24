import app.graph.graph
from app.tools.financial import get_company_info


def test_get_company_info_returns_company_data():
    result = get_company_info.invoke(
        {"ticker": "AAPL"}
    )

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["sector"] == "Technology"


def test_get_company_info_requires_ticker():
    schema = get_company_info.args_schema

    assert "ticker" in schema.model_fields


def test_get_company_info_invalid_ticker():
    import pytest

    with pytest.raises(
        ValueError,
        match="Company information not found",
    ):
        get_company_info.invoke(
            {"ticker": "INVALID"}
        )


from langchain_core.messages import HumanMessage

from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


def test_llm_selects_stock_price_tool():
    llm = app.graph.graph.llm

    llm_with_tools = llm.bind_tools(
        [
            get_stock_price,
            get_company_info,
        ]
    )

    response = llm_with_tools.invoke(
        [
            HumanMessage(
                content="What is the current stock price of AAPL?"
            )
        ]
    )

    assert response.tool_calls

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_stock_price"
    assert tool_call["args"]["ticker"] == "AAPL"


def test_llm_selects_company_info_tool():
    llm = app.graph.graph.llm

    llm_with_tools = llm.bind_tools(
        [
            get_stock_price,
            get_company_info,
        ]
    )

    response = llm_with_tools.invoke(
        [
            HumanMessage(
                content=(
                    "What company is AAPL and "
                    "what sector does it belong to?"
                )
            )
        ]
    )

    assert response.tool_calls

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "get_company_info"
    assert tool_call["args"]["ticker"] == "AAPL"