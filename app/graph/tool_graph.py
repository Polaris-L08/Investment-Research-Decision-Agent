from langgraph.graph import StateGraph, START, END

from app.graph.graph import handle_tool_failure
from app.graph.nodes.tool_node import (
    get_stock_price_node,
    route_after_tool,
)
from app.graph.state import GraphState


def build_tool_graph():
    builder = StateGraph(GraphState)

    builder.add_node(
        "get_stock_price",
        get_stock_price_node,
    )

    builder.add_node(
        "tool_failure",
        handle_tool_failure,
    )

    builder.add_edge(
        START,
        "get_stock_price",
    )

    builder.add_conditional_edges(
        "get_stock_price",
        route_after_tool,
        {
            "success": END,
            "retry": "get_stock_price",
            "failure": "tool_failure",
        },
    )

    builder.add_edge(
        "tool_failure",
        END,
    )

    return builder.compile()