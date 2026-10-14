
from typing import Literal, TypedDict

from pydantic import BaseModel

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str
    confidence: int


class ApprovalState(TypedDict):
    request_id: str
    schema_mode: str
    decision: str
    reason: str
    confidence: int


def build_graph():
    def approval_node(state: ApprovalState):
        print(f"\n[approval] request={state['request_id']}")

        if state["schema_mode"] == "pydantic":
            response = interrupt(
                {
                    "question": "是否批准继续研究？",
                    "request_id": state["request_id"],
                },
                response_schema=ApprovalDecision,
            )
        else:
            response = interrupt(
                {
                    "question": "是否批准继续研究？",
                    "request_id": state["request_id"],
                }
            )

        print("Response type:", type(response))
        print("Response repr:", repr(response))

        if isinstance(response, ApprovalDecision):
            decision = response.decision
            reason = response.reason
            confidence = response.confidence
        else:
            decision = response["decision"]
            reason = response["reason"]
            confidence = response["confidence"]

        return {
            "decision": decision,
            "reason": reason,
            "confidence": confidence,
        }

    builder = StateGraph(ApprovalState)
    builder.add_node("approval", approval_node)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)

    return builder.compile(checkpointer=InMemorySaver())


def initial_input(request_id: str, schema_mode: str):
    return {
        "request_id": request_id,
        "schema_mode": schema_mode,
        "decision": "",
        "reason": "",
        "confidence": 0,
    }


def run_valid_case(graph, thread_id, schema_mode, payload):
    print("\n" + "=" * 65)
    print(f"VALID CASE: mode={schema_mode}, payload={payload!r}")
    print("=" * 65)

    config = {"configurable": {"thread_id": thread_id}}

    graph.invoke(
        initial_input(thread_id, schema_mode),
        config=config,
    )

    paused = graph.get_state(config)
    print("Paused next:", paused.next)
    print("Interrupts:", paused.interrupts)

    assert paused.next == ("approval",)

    result = graph.invoke(
        Command(resume=payload),
        config=config,
    )

    print("Final result:", result)
    print("Final next:", graph.get_state(config).next)

    assert result["decision"] == "approve"
    assert graph.get_state(config).next == ()

    print("PASS: Valid response completed.")


def run_invalid_schema_case(graph):
    thread_id = "p10-d2-invalid-schema"
    config = {"configurable": {"thread_id": thread_id}}

    print("\n" + "=" * 65)
    print("INVALID CASE: Pydantic response_schema")
    print("=" * 65)

    graph.invoke(
        initial_input(thread_id, "pydantic"),
        config=config,
    )

    invalid_payload = {
        "decision": "maybe",
        "reason": "invalid decision",
        "confidence": 3,
    }

    try:
        graph.invoke(
            Command(resume=invalid_payload),
            config=config,
        )
    except Exception as exc:
        print("Exception type:", type(exc).__name__)
        print("Exception:", str(exc))
    else:
        raise AssertionError(
            "Expected invalid response to be rejected."
        )

    snapshot = graph.get_state(config)
    print("State after invalid response:", snapshot.values)
    print("Next after invalid response:", snapshot.next)
    print("Interrupts after invalid response:", snapshot.interrupts)

    assert snapshot.values["decision"] == ""
    print("PASS: Invalid response did not set the decision.")

    if snapshot.next == ("approval",):
        print("\nRetrying with a valid response on the same thread...")

        result = graph.invoke(
            Command(
                resume={
                    "decision": "reject",
                    "reason": "Corrected response",
                    "confidence": 2,
                }
            ),
            config=config,
        )

        print("Retry result:", result)
        print("Next after retry:", graph.get_state(config).next)
    else:
        print(
            "Observation: approval is not listed in snapshot.next. "
            "This checkpoint does not currently report the node "
            "as pending; no retry is assumed."
        )


def main():
    graph = build_graph()

    # No response_schema: raw dictionary is returned.
    run_valid_case(
        graph,
        "p10-d2-raw",
        "raw",
        {
            "decision": "approve",
            "reason": "Raw dictionary response",
            "confidence": 3,
        },
    )

    # Pydantic schema: confidence is supplied as a numeric string.
    run_valid_case(
        graph,
        "p10-d2-pydantic",
        "pydantic",
        {
            "decision": "approve",
            "reason": "Validated Pydantic response",
            "confidence": "3",
        },
    )

    # Pydantic schema: invalid Literal value.
    run_invalid_schema_case(graph)

    print("\n" + "=" * 65)
    print("PASS: Response-schema experiments completed.")
    print("=" * 65)


if __name__ == "__main__":
    main()
