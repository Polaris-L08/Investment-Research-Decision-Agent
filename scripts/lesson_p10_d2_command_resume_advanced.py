
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    request_id: str
    approval_ticket_id: str
    approval_decision: str
    fundamental_decision: str
    risk_decision: str


def build_single_interrupt_graph():
    def approval_node(state: ApprovalState):
        print(
            "[approval] ticket_id =",
            state["approval_ticket_id"],
        )

        response = interrupt({
            "request_id": state["request_id"],
            "question": "是否批准继续研究？",
        })

        return {
            "approval_decision": response["decision"],
        }

    builder = StateGraph(ApprovalState)
    builder.add_node("approval", approval_node)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)

    return builder.compile(checkpointer=InMemorySaver())


def build_parallel_interrupt_graph():
    def fundamental_review(state: ApprovalState):
        response = interrupt({
            "type": "fundamental_review",
            "question": "是否接受基本面研究假设？",
        })
        return {"fundamental_decision": response["decision"]}

    def risk_review(state: ApprovalState):
        response = interrupt({
            "type": "risk_review",
            "question": "是否接受风险评估？",
        })
        return {"risk_decision": response["decision"]}

    builder = StateGraph(ApprovalState)
    builder.add_node("fundamental_review", fundamental_review)
    builder.add_node("risk_review", risk_review)

    builder.add_edge(START, "fundamental_review")
    builder.add_edge(START, "risk_review")
    builder.add_edge("fundamental_review", END)
    builder.add_edge("risk_review", END)

    return builder.compile(checkpointer=InMemorySaver())


def initial_state(request_id: str):
    return {
        "request_id": request_id,
        "approval_ticket_id": "",
        "approval_decision": "",
        "fundamental_decision": "",
        "risk_decision": "",
    }


def test_resume_with_update():
    print("\n" + "=" * 65)
    print("TEST 1: Command(resume=..., update=...)")
    print("=" * 65)

    graph = build_single_interrupt_graph()
    config = {
        "configurable": {
            "thread_id": "p10-d2-resume-update",
        }
    }

    graph.invoke(
        initial_state("REQ-001"),
        config=config,
    )

    snapshot = graph.get_state(config)
    print("Interrupts:", snapshot.interrupts)

    assert snapshot.next == ("approval",)

    result = graph.invoke(
        Command(
            resume={
                "decision": "approve",
            },
            update={
                "approval_ticket_id": "APR-2026-001",
            },
        ),
        config=config,
    )

    print("Result:", result)
    print("Final next:", graph.get_state(config).next)

    assert result["approval_decision"] == "approve"
    assert result["approval_ticket_id"] == "APR-2026-001"
    assert graph.get_state(config).next == ()

    print("PASS: Resume and state update completed.")


def test_resume_multiple_interrupts():
    print("\n" + "=" * 65)
    print("TEST 2: Resume multiple interrupts by ID")
    print("=" * 65)

    graph = build_parallel_interrupt_graph()
    config = {
        "configurable": {
            "thread_id": "p10-d2-multiple-interrupts",
        }
    }

    graph.invoke(
        initial_state("REQ-002"),
        config=config,
    )

    snapshot = graph.get_state(config)

    print("Pending nodes:", snapshot.next)

    interrupts_by_type = {}

    for item in snapshot.interrupts:
        print("Interrupt ID:", item.id)
        print("Interrupt payload:", item.value)

        interrupts_by_type[item.value["type"]] = item.id

    assert len(interrupts_by_type) == 2
    assert snapshot.next

    resume_values = {
        interrupts_by_type["fundamental_review"]: {
            "decision": "approve",
        },
        interrupts_by_type["risk_review"]: {
            "decision": "reject",
        },
    }

    result = graph.invoke(
        Command(resume=resume_values),
        config=config,
    )

    print("Result:", result)
    print("Final next:", graph.get_state(config).next)

    assert result["fundamental_decision"] == "approve"
    assert result["risk_decision"] == "reject"
    assert graph.get_state(config).next == ()

    print("PASS: Both interrupts were resumed by ID.")


def main():
    test_resume_with_update()
    test_resume_multiple_interrupts()

    print("\n" + "=" * 65)
    print("PASS: Advanced Command experiments completed.")
    print("=" * 65)


if __name__ == "__main__":
    main()
