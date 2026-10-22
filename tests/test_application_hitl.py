
import app.application.graph as application_graph_module
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.application.graph import build_application_graph


def build_paused_application(monkeypatch):
    research_calls = []

    def fake_research(state):
        research_calls.append(state["ticker"])
        return {
            "current_stage": "research",
            "stage_errors": {
                **dict(state.get("stage_errors") or {}),
                "research": "Stopped by test double.",
            },
            "application_error": "research failed: Stopped by test double.",
        }

    monkeypatch.setattr(
        application_graph_module,
        "run_research_stage",
        fake_research,
    )

    graph = build_application_graph(checkpointer=MemorySaver())
    config = {
        "configurable": {
            "thread_id": "application-hitl-test"
        }
    }

    graph.invoke(
        {
            "ticker": "AAPL",
            "user_query": "Analyze the company's financial condition.",
        },
        config,
    )

    return graph, config, research_calls


def test_application_graph_pauses_before_research(monkeypatch):
    graph, config, research_calls = build_paused_application(monkeypatch)

    snapshot = graph.get_state(config)
    pending_interrupts = [
        item
        for task in snapshot.tasks
        for item in task.interrupts
    ]

    assert pending_interrupts
    payload = pending_interrupts[0].value

    assert payload["type"] == "research_approval"
    assert payload["ticker"] == "AAPL"
    assert payload["requested_action"] == "run_research"
    assert snapshot.values["approval_status"] == "pending"
    assert research_calls == []


def test_application_graph_approval_enters_research(monkeypatch):
    graph, config, research_calls = build_paused_application(monkeypatch)

    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "reason": "Research approved for execution.",
            }
        ),
        config,
    )

    assert result["approval_status"] == "approved"
    assert result["execution_status"] == "failed"
    assert result["approval_reason"] == "Research approved for execution."
    assert research_calls == ["AAPL"]


def test_application_graph_rejection_skips_research(monkeypatch):
    graph, config, research_calls = build_paused_application(monkeypatch)

    result = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "reason": "Request needs clarification.",
            }
        ),
        config,
    )

    assert result["approval_status"] == "rejected"
    assert result["execution_status"] == "rejected"
    assert result["approval_reason"] == "Request needs clarification."
    assert result["application_error"] == ""
    assert research_calls == []


def test_application_graph_invalid_decision_skips_research(monkeypatch):
    graph, config, research_calls = build_paused_application(monkeypatch)

    result = graph.invoke(
        Command(
            resume={
                "decision": "maybe",
                "reason": "Unclear decision.",
            }
        ),
        config,
    )

    assert result["approval_status"] == "invalid"
    assert result["execution_status"] == "failed"
    assert "Approval failed" in result["application_error"]
    assert research_calls == []
