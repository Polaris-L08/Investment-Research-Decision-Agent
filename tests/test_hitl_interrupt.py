
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ApprovalTestState(TypedDict, total=False):
    ticker: str
    research_task: str
    approval_gate_passed: bool
    research_executed: bool


def approval_gate(state: ApprovalTestState) -> dict:
    """Pause execution and request human approval."""

    interrupt(
        {
            "type": "research_approval",
            "ticker": state["ticker"],
            "research_task": state["research_task"],
            "reason_for_approval": "The research task requires human approval.",
            "requested_action": "run_research",
            "approval_required": True,
        }
    )

    # This line is reached only after the interrupt is resumed.
    return {"approval_gate_passed": True}


def run_research(state: ApprovalTestState) -> dict:
    """Represent a downstream research node without real external calls."""

    return {"research_executed": True}


def build_hitl_test_graph():
    builder = StateGraph(ApprovalTestState)

    builder.add_node("approval_gate", approval_gate)
    builder.add_node("research", run_research)

    builder.add_edge(START, "approval_gate")
    builder.add_edge("approval_gate", "research")
    builder.add_edge("research", END)

    return builder.compile(checkpointer=MemorySaver())


def test_interrupt_pauses_before_research():
    graph = build_hitl_test_graph()

    config = {
        "configurable": {
            "thread_id": "hitl-lesson-2-test"
        }
    }

    result = graph.invoke(
        {
            "ticker": "AAPL",
            "research_task": "Analyze financial condition and competition.",
            "approval_gate_passed": False,
            "research_executed": False,
        },
        config,
    )

    snapshot = graph.get_state(config)

    # The graph must have a pending interrupt.
    pending_interrupts = [
        item
        for task in snapshot.tasks
        for item in task.interrupts
    ]
    assert pending_interrupts

    # The caller must be able to inspect the approval request.
    payload = pending_interrupts[0].value
    assert payload["type"] == "research_approval"
    assert payload["ticker"] == "AAPL"
    assert payload["requested_action"] == "run_research"
    assert payload["approval_required"] is True

    # The graph must not have executed the research node.
    assert result.get("research_executed") is False
    assert snapshot.values.get("research_executed") is False
    assert snapshot.values.get("approval_gate_passed") is False
