from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.graph.graph import llm
from app.tools.financial import (
    get_company_info,
    get_stock_price,
)
from app.tools.registry import TOOLS


class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm_with_tools = llm.bind_tools(TOOLS)

tool_node = ToolNode(TOOLS)


def tool_loop_llm_node(state: ToolLoopState):
    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


def route_after_llm(state: ToolLoopState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


def build_tool_loop_graph():
    builder = StateGraph(ToolLoopState)

    builder.add_node(
        "llm",
        tool_loop_llm_node,
    )

    builder.add_node(
        "tools",
        tool_node,
    )

    builder.add_edge(
        START,
        "llm",
    )

    builder.add_conditional_edges(
        "llm",
        route_after_llm,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge(
        "tools",
        "llm",
    )

    return builder.compile()