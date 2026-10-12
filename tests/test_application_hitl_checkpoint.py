
import sqlite3

import pytest
import app.application.graph as application_graph_module
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from app.application.graph import build_application_graph


def build_test_graph(database_path, monkeypatch, research_calls):
    """Build the production Application Graph with SQLite persistence."""

    def fake_research(state):
        research_calls.append(state["ticker"])
        return {
            "current_stage": "research",
            "stage_errors": {
                **dict(state.get("stage_errors") or {}),
                "research": "Stopped by checkpoint test double.",
            },
            "application_error": (
                "research failed: Stopped by checkpoint test double."
            ),
        }

    monkeypatch.setattr(
        application_graph_module,
        "run_research_stage",
        fake_research,
    )

    connection = sqlite3.connect(
        database_path,
        check_same_thread=False,
    )
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()

    graph = build_application_graph(checkpointer=checkpointer)
    return graph, connection


@pytest.mark.parametrize(
    ("decision", "expected_status", "should_run_research"),
    [
        ("approve", "approved", True),
        ("reject", "rejected", False),
    ],
)
def test_hitl_checkpoint_survives_graph_recreation(
    tmp_path,
    monkeypatch,
    decision,
    expected_status,
    should_run_research,
):
    database_path = tmp_path / "hitl-checkpoints.sqlite"
    thread_id = f"checkpoint-{decision}"
    config = {"configurable": {"thread_id": thread_id}}
    research_calls = []

    # First Graph instance: execute until the approval interrupt.
    graph_1, connection_1 = build_test_graph(
        database_path,
        monkeypatch,
        research_calls,
    )

    try:
        graph_1.invoke(
            {
                "ticker": "AAPL",
                "user_query": "Analyze financial condition and competition.",
            },
            config,
        )

        snapshot_1 = graph_1.get_state(config)
        assert snapshot_1.values["approval_status"] == "pending"
        assert snapshot_1.tasks
        assert research_calls == []
    finally:
        connection_1.close()

    # Second Graph instance: reopen the same SQLite database.
    graph_2, connection_2 = build_test_graph(
        database_path,
        monkeypatch,
        research_calls,
    )

    try:
        # The pending approval must survive connection and Graph recreation.
        snapshot_2 = graph_2.get_state(config)

        assert snapshot_2.values["ticker"] == "AAPL"
        assert snapshot_2.values["approval_status"] == "pending"

        pending_interrupts = [
            item
            for task in snapshot_2.tasks
            for item in task.interrupts
        ]
        assert pending_interrupts
        assert pending_interrupts[0].value["type"] == "research_approval"

        # Resume the existing thread, not a new execution.
        result = graph_2.invoke(
            Command(
                resume={
                    "decision": decision,
                    "reason": "Decision submitted after graph recreation.",
                }
            ),
            config,
        )

        assert result["approval_status"] == expected_status

        if should_run_research:
            assert research_calls == ["AAPL"]
        else:
            assert research_calls == []

    finally:
        connection_2.close()


def test_hitl_checkpoint_threads_are_isolated(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "hitl-thread-isolation.sqlite"
    research_calls = []

    graph, connection = build_test_graph(
        database_path,
        monkeypatch,
        research_calls,
    )

    config_a = {"configurable": {"thread_id": "approval-thread-a"}}
    config_b = {"configurable": {"thread_id": "approval-thread-b"}}

    try:
        graph.invoke(
            {
                "ticker": "AAPL",
                "user_query": "Research Apple.",
            },
            config_a,
        )
        graph.invoke(
            {
                "ticker": "MSFT",
                "user_query": "Research Microsoft.",
            },
            config_b,
        )

        snapshot_a = graph.get_state(config_a)
        snapshot_b = graph.get_state(config_b)

        assert snapshot_a.values["ticker"] == "AAPL"
        assert snapshot_b.values["ticker"] == "MSFT"
        assert snapshot_a.values["approval_status"] == "pending"
        assert snapshot_b.values["approval_status"] == "pending"

        result_a = graph.invoke(
            Command(
                resume={
                    "decision": "approve",
                    "reason": "Approved AAPL.",
                }
            ),
            config_a,
        )

        assert result_a["approval_status"] == "approved"
        assert research_calls == ["AAPL"]

        # Resuming thread A must not resume thread B.
        snapshot_b_after = graph.get_state(config_b)
        assert snapshot_b_after.values["ticker"] == "MSFT"
        assert snapshot_b_after.values["approval_status"] == "pending"

        result_b = graph.invoke(
            Command(
                resume={
                    "decision": "reject",
                    "reason": "Rejected MSFT.",
                }
            ),
            config_b,
        )

        assert result_b["approval_status"] == "rejected"
        assert research_calls == ["AAPL"]

    finally:
        connection.close()
