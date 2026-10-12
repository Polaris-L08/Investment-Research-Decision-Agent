
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalTestState(TypedDict, total=False):
    ticker: str
    research_task: str
    approval_status: str
    approval_reason: str
    research_executed: bool


def approval_gate(state: ApprovalTestState) -> dict:
    """Pause and validate the resumed approval decision."""

    decision = interrupt(
        {
            "type": "research_approval",
            "ticker": state["ticker"],
            "research_task": state["research_task"],
            "reason_for_approval": "The research task requires human approval.",
            "requested_action": "run_research",
            "approval_required": True,
        }
    )

    # Do not trust the resumed value without validation.
    if not isinstance(decision, dict):
        return {
            "approval_status": "invalid",
            "approval_reason": "Approval response must be a dictionary.",
        }

    action = decision.get("decision")
    reason = decision.get("reason", "")

    if action not in {"approve", "reject"}:
        return {
            "approval_status": "invalid",
            "approval_reason": "Decision must be 'approve' or 'reject'.",
        }

    if not isinstance(reason, str):
        return {
            "approval_status": "invalid",
            "approval_reason": "Approval reason must be a string.",
        }

    return {
        "approval_status": action,
        "approval_reason": reason,
    }


def run_research(state: ApprovalTestState) -> dict:
    """Represent research without calling external services."""
    return {"research_executed": True}


def record_rejection(state: ApprovalTestState) -> dict:
    """Record that the request was rejected."""
    return {"research_executed": False}


def record_invalid_decision(state: ApprovalTestState) -> dict:
    """Record that the approval response was invalid."""
    return {"research_executed": False}


def route_after_approval(state: ApprovalTestState) -> str:
    status = state.get("approval_status")

    if status == "approve":
        return "research"
    if status == "reject":
        return "rejected"
    return "invalid"


def build_hitl_test_graph():
    builder = StateGraph(ApprovalTestState)

    builder.add_node("approval_gate", approval_gate)
    builder.add_node("research", run_research)
    builder.add_node("rejected", record_rejection)
    builder.add_node("invalid", record_invalid_decision)

    builder.add_edge(START, "approval_gate")

    builder.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "research": "research",
            "rejected": "rejected",
            "invalid": "invalid",
        },
    )

    builder.add_edge("research", END)
    builder.add_edge("rejected", END)
    builder.add_edge("invalid", END)

    return builder.compile(checkpointer=MemorySaver())


def start_paused_graph():
    graph = build_hitl_test_graph()
    config = {
        "configurable": {
            "thread_id": "hitl-lesson-3-test"
        }
    }

    graph.invoke(
        {
            "ticker": "AAPL",
            "research_task": "Analyze financial condition and competition.",
            "approval_status": "pending",
            "research_executed": False,
        },
        config,
    )

    return graph, config


def test_approve_resumes_and_executes_research():
    graph, config = start_paused_graph()

    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
                "reason": "Research request approved.",
            }
        ),
        config,
    )

    assert result["approval_status"] == "approve"
    assert result["approval_reason"] == "Research request approved."
    assert result["research_executed"] is True


def test_reject_resumes_without_executing_research():
    graph, config = start_paused_graph()

    result = graph.invoke(
        Command(
            resume={
                "decision": "reject",
                "reason": "Research request needs revision.",
            }
        ),
        config,
    )

    assert result["approval_status"] == "reject"
    assert result["research_executed"] is False


def test_invalid_decision_does_not_execute_research():
    graph, config = start_paused_graph()

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
    assert result["research_executed"] is False


def test_non_dictionary_resume_does_not_execute_research():
    graph, config = start_paused_graph()

    result = graph.invoke(
        Command(resume="approve"),
        config,
    )

    assert result["approval_status"] == "invalid"
    assert result["research_executed"] is False
