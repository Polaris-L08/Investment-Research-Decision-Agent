from langchain_core.messages import BaseMessage

from app.graph.graph import llm
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)


llm_with_tools = llm.bind_tools(
    [
        get_stock_price,
        get_company_info,
    ]
)


def tool_loop_llm_node(
    state: dict,
) -> dict:
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }