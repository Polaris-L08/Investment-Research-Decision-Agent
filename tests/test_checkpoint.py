import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from typing import TypedDict

from app.graph.checkpointer import create_checkpointer
from app.graph.graph import graph


class CounterState(TypedDict):
    value: int


def build_test_graph(checkpointer):
    builder = StateGraph(CounterState)

    def increment(state: CounterState):
        return {
            "value": state["value"] + 1,
        }

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    return builder.compile(
        checkpointer=checkpointer,
    )


def test_main_application_graph_has_checkpointer():
    assert graph.checkpointer is not None


def test_sqlite_checkpointer_persists_state(tmp_path):
    database_path = tmp_path / "checkpoints.sqlite"

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    # checkpointer = SqliteSaver(connection)
    checkpointer = create_checkpointer()

    test_graph = build_test_graph(checkpointer)

    config = {
        "configurable": {
            "thread_id": "sqlite-test-thread",
        }
    }

    result = test_graph.invoke(
        {"value": 0},
        config,
    )

    assert result["value"] == 1

    snapshot = test_graph.get_state(config)

    assert snapshot.values["value"] == 1


def test_sqlite_checkpoint_survives_graph_recreation(tmp_path):
    database_path = tmp_path / "restart-test.sqlite"

    config = {
        "configurable": {
            "thread_id": "restart-test-thread",
        }
    }

    connection_1 = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer_1 = SqliteSaver(connection_1)

    graph_1 = build_test_graph(checkpointer_1)

    result_1 = graph_1.invoke(
        {"value": 10},
        config,
    )

    assert result_1["value"] == 11

    connection_1.close()

    connection_2 = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer_2 = SqliteSaver(connection_2)

    graph_2 = build_test_graph(checkpointer_2)

    snapshot = graph_2.get_state(config)

    assert snapshot.values["value"] == 11

    connection_2.close()


def test_sqlite_threads_are_isolated(tmp_path):
    database_path = tmp_path / "thread-isolation.sqlite"

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(connection)

    test_graph = build_test_graph(checkpointer)

    thread_a = {
        "configurable": {
            "thread_id": "sqlite-thread-a",
        }
    }

    thread_b = {
        "configurable": {
            "thread_id": "sqlite-thread-b",
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

    connection.close()