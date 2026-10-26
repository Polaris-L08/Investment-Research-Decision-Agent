"""Phase 13, Lesson 13.3: inspect LangGraph execution events."""

import asyncio
from importlib.metadata import PackageNotFoundError, version
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class DemoState(TypedDict):
    value: int
    route: Literal["left", "right"]


def choose_route(state: DemoState) -> dict:
    """Choose a branch without performing external calls."""
    return {"route": "left" if state["value"] >= 0 else "right"}


def normal_node(state: DemoState) -> dict:
    """A node that completes normally."""
    return {"value": state["value"] + 1}


def left_node(state: DemoState) -> dict:
    """The selected branch for non-negative values."""
    return {"value": state["value"] * 2}


def right_node(state: DemoState) -> dict:
    """The alternative branch."""
    return {"value": state["value"] - 10}


def failing_node(state: DemoState) -> dict:
    """A node that deliberately raises an exception."""
    raise ValueError("lesson_p13_d3_deliberate_failure")


def build_normal_graph():
    builder = StateGraph(DemoState)

    builder.add_node("choose_route", choose_route)
    builder.add_node("normal_node", normal_node)
    builder.add_node("left_node", left_node)
    builder.add_node("right_node", right_node)

    builder.add_edge(START, "choose_route")
    builder.add_edge("choose_route", "normal_node")

    builder.add_conditional_edges(
        "normal_node",
        lambda state: state["route"],
        {
            "left": "left_node",
            "right": "right_node",
        },
    )

    builder.add_edge("left_node", END)
    builder.add_edge("right_node", END)

    return builder.compile()


def build_failing_graph():
    builder = StateGraph(DemoState)

    builder.add_node("normal_node", normal_node)
    builder.add_node("failing_node", failing_node)

    builder.add_edge(START, "normal_node")
    builder.add_edge("normal_node", "failing_node")
    builder.add_edge("failing_node", END)

    return builder.compile()


def print_event(event: dict) -> None:
    """Print event metadata without dumping full state or payloads."""
    metadata = event.get("metadata") or {}
    data = event.get("data") or {}

    print(
        {
            "event": event.get("event"),
            "name": event.get("name"),
            "run_id": event.get("run_id"),
            "parent_ids": event.get("parent_ids"),
            "langgraph_node": metadata.get("langgraph_node"),
            "langgraph_step": metadata.get("langgraph_step"),
            "data_keys": sorted(data.keys()),
        }
    )


async def observe_graph(label: str, graph, initial_state: DemoState) -> None:
    print(f"\n{'=' * 20} {label} {'=' * 20}")

    try:
        async for event in graph.astream_events(
            initial_state,
            version="v2",
            config={"run_name": label},
        ):
            print_event(event)

    except Exception as exc:
        print(
            {
                "observer": "outer_exception",
                "exception_type": type(exc).__name__,
                "message": str(exc),
            }
        )


async def main() -> None:
    for package_name in ("langgraph", "langchain-core"):
        try:
            print(f"{package_name} version: {version(package_name)}")
        except PackageNotFoundError:
            print(f"{package_name} version: not installed")

    normal_graph = build_normal_graph()
    failing_graph = build_failing_graph()

    # Run A: the left branch should execute.
    await observe_graph(
        "lesson_p13_d3_normal",
        normal_graph,
        {"value": 1, "route": "left"},
    )

    # Run B: the graph should raise the deliberate ValueError.
    await observe_graph(
        "lesson_p13_d3_failing",
        failing_graph,
        {"value": 1, "route": "left"},
    )


if __name__ == "__main__":
    asyncio.run(main())