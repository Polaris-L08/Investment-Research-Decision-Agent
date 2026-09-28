from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.llm.client import llm
from app.tools.registry import TOOLS


class ToolLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_tool_loop_graph(tools):

    llm_with_tools = llm.bind_tools(tools)

    tool_node = ToolNode(tools=tools)

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