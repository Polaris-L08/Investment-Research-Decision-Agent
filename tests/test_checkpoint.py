from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.graph import graph


class CounterState(TypedDict):
    value: int


def build_test_graph():
    builder = StateGraph(CounterState)

    def increment(state: CounterState):
        return {
            "value": state["value"] + 1,
        }

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )


def test_main_application_graph_has_checkpointer():
    assert graph.checkpointer is not None


def test_checkpointer_persists_state_for_a_thread():
    test_graph = build_test_graph()

    config = {
        "configurable": {
            "thread_id": "checkpoint-test-thread",
        }
    }

    result = test_graph.invoke(
        {"value": 0},
        config,
    )

    assert result["value"] == 1

    snapshot = test_graph.get_state(config)

    assert snapshot.values["value"] == 1
    assert snapshot.config["configurable"]["thread_id"] == (
        "checkpoint-test-thread"
    )


def test_threads_are_isolated():
    test_graph = build_test_graph()

    thread_a = {
        "configurable": {
            "thread_id": "thread-a",
        }
    }

    thread_b = {
        "configurable": {
            "thread_id": "thread-b",
        }
    }

    result_a = test_graph.invoke(
        {"value": 10},
        thread_a,
    )

    result_b = test_graph.invoke(
        {"value": 20},
        thread_b,
    )

    assert result_a["value"] == 11
    assert result_b["value"] == 21

    snapshot_a = test_graph.get_state(thread_a)
    snapshot_b = test_graph.get_state(thread_b)

    assert snapshot_a.values["value"] == 11
    assert snapshot_b.values["value"] == 21

    assert (
        snapshot_a.config["configurable"]["thread_id"]
        == "thread-a"
    )

    assert (
        snapshot_b.config["configurable"]["thread_id"]
        == "thread-b"
    )