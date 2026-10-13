
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    request_id: str
    approval_status: str
    approval_reason: str


def validate_resume_value(value: object) -> dict[str, str]:
    """Validate the payload returned by interrupt()."""

    if not isinstance(value, dict):
        raise ValueError("Resume value must be a dictionary")

    decision = value.get("decision")
    reason = value.get("reason")

    if not isinstance(decision, str):
        raise ValueError("decision must be a string")

    if decision not in ("approve", "reject"):
        raise ValueError(
            "decision must be 'approve' or 'reject'"
        )

    if not isinstance(reason, str):
        raise ValueError("reason must be a string")

    return {
        "decision": decision,
        "reason": reason,
    }


def build_graph():
    def approval_node(state: ApprovalState):
        print(f"[approval] waiting for {state['request_id']}")

        resume_value = interrupt(
            {
                "request_id": state["request_id"],
                "question": "Approve this request?",
                "allowed_decisions": ["approve", "reject"],
                "required_fields": {
                    "decision": "string",
                    "reason": "string",
                },
            }
        )

        # Validate before changing business state.
        validated = validate_resume_value(resume_value)

        if validated["decision"] == "approve":
            status = "approved"
        else:
            status = "rejected"

        print(
            f"[approval] validated decision={validated['decision']}"
        )

        return {
            "approval_status": status,
            "approval_reason": validated["reason"],
        }

    builder = StateGraph(ApprovalState)
    builder.add_node("approval", approval_node)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)

    return builder.compile(checkpointer=InMemorySaver())


def initial_input(request_id: str):
    return {
        "request_id": request_id,
        "approval_status": "pending",
        "approval_reason": "",
    }


def resume_payload(decision: str, reason: str):
    return {
        "decision": decision,
        "reason": reason,
    }


def run_valid_case(graph, thread_id, decision):
    print("\n" + "=" * 60)
    print(f"VALID CASE: {decision}")
    print("=" * 60)

    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(initial_input(thread_id), config=config)

    snapshot = graph.get_state(config)
    assert snapshot.next == ("approval",)

    result = graph.invoke(
        Command(
            resume=resume_payload(
                decision,
                f"Test reason for {decision}",
            )
        ),
        config=config,
    )

    expected_status = (
        "approved" if decision == "approve" else "rejected"
    )

    print("Final result:", result)
    print("Final next:", graph.get_state(config).next)

    assert result["approval_status"] == expected_status
    assert result["approval_reason"] == (
        f"Test reason for {decision}"
    )
    assert graph.get_state(config).next == ()

    print(f"PASS: {decision} was handled correctly.")


def run_invalid_case(graph, thread_id, invalid_value):
    print("\n" + "=" * 60)
    print(f"INVALID CASE: {invalid_value!r}")
    print("=" * 60)

    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(initial_input(thread_id), config=config)

    snapshot = graph.get_state(config)
    assert snapshot.next == ("approval",)

    try:
        graph.invoke(
            Command(resume=invalid_value),
            config=config,
        )
    except ValueError as exc:
        print("Rejected invalid resume value:", exc)
    else:
        raise AssertionError(
            "Expected invalid resume value to raise ValueError"
        )

    # Inspect the state after the failed resume attempt.
    snapshot = graph.get_state(config)
    print("State after invalid input:", snapshot.values)
    print("Next after invalid input:", snapshot.next)

    assert snapshot.values["approval_status"] == "pending"
    assert snapshot.next == ("approval",)

    # Retry with a valid payload on the same thread.
    print("Retrying with a valid rejection payload...")

    result = graph.invoke(
        Command(
            resume=resume_payload(
                "reject",
                "Corrected input after validation failure",
            )
        ),
        config=config,
    )

    print("Result after retry:", result)

    assert result["approval_status"] == "rejected"
    assert graph.get_state(config).next == ()

    print("PASS: Invalid input was rejected; valid retry succeeded.")


def main():
    graph = build_graph()

    run_valid_case(
        graph,
        "p10-d2-valid-approve",
        "approve",
    )

    run_valid_case(
        graph,
        "p10-d2-valid-reject",
        "reject",
    )

    invalid_values = [
        "approve",
        {},
        {"decision": "maybe", "reason": "test"},
        {"decision": 123, "reason": "test"},
        {"decision": "approve", "reason": 123},
    ]

    for index, invalid_value in enumerate(invalid_values, start=1):
        run_invalid_case(
            graph,
            f"p10-d2-invalid-{index}",
            invalid_value,
        )

    print("\n" + "=" * 60)
    print("PASS: All P10-D2 validation experiments completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
