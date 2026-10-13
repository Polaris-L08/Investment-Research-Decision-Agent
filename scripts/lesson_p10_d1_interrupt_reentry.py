
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    request_id: str
    prepared: bool
    approval_decision: str


def main():
    # These counters are external to LangGraph state.
    # They let us observe actual Python function executions.
    execution_counts = {
        "prepare": 0,
        "approval_before_interrupt": 0,
        "approval_after_interrupt": 0,
    }

    def prepare(state: ApprovalState):
        execution_counts["prepare"] += 1
        print(
            f"[prepare] execution "
            f"#{execution_counts['prepare']}"
        )

        return {"prepared": True}

    def approval(state: ApprovalState):
        execution_counts["approval_before_interrupt"] += 1
        print(
            "[approval] before interrupt: execution "
            f"#{execution_counts['approval_before_interrupt']}"
        )

        resume_value = interrupt(
            {
                "request_id": state["request_id"],
                "question": "Approve this investment research request?",
                "allowed_decisions": ["approve", "reject"],
            }
        )

        execution_counts["approval_after_interrupt"] += 1
        print(
            "[approval] after interrupt: execution "
            f"#{execution_counts['approval_after_interrupt']}"
        )
        print(f"[approval] received resume value: {resume_value}")

        if not isinstance(resume_value, dict):
            raise ValueError("Resume value must be a dictionary")

        decision = resume_value.get("decision")
        if decision not in ("approve", "reject"):
            raise ValueError("Decision must be approve or reject")

        return {"approval_decision": decision}

    builder = StateGraph(ApprovalState)
    builder.add_node("prepare", prepare)
    builder.add_node("approval", approval)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "approval")
    builder.add_edge("approval", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "p10-d1-reentry-demo"
        }
    }

    print("\n===== 1. First invocation: expect interrupt =====")
    result1 = graph.invoke(
        {
            "request_id": "REQ-001",
            "prepared": False,
            "approval_decision": "",
        },
        config=config,
    )

    print("First invocation returned:", result1)
    print("Execution counts after interrupt:", execution_counts)

    snapshot = graph.get_state(config)
    print("Snapshot values:", snapshot.values)
    print("Snapshot next:", snapshot.next)

    assert execution_counts["prepare"] == 1
    assert execution_counts["approval_before_interrupt"] == 1
    assert execution_counts["approval_after_interrupt"] == 0
    assert snapshot.next == ("approval",)

    print("\n===== 2. Resume the interrupted thread =====")
    result2 = graph.invoke(
        Command(resume={"decision": "approve"}),
        config=config,
    )

    print("Final result:", result2)
    print("Final execution counts:", execution_counts)

    assert execution_counts["prepare"] == 1
    assert execution_counts["approval_before_interrupt"] == 2
    assert execution_counts["approval_after_interrupt"] == 1
    assert result2["approval_decision"] == "approve"

    final_snapshot = graph.get_state(config)
    print("Final snapshot next:", final_snapshot.next)

    assert final_snapshot.next == ()

    print("\nPASS: Interrupt node re-entry behavior verified.")


if __name__ == "__main__":
    main()
