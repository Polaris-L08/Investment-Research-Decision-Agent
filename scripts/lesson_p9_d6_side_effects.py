
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class OperationState(TypedDict):
    operation_key: str
    status: str


def build_graph(node, checkpointer):
    builder = StateGraph(OperationState)
    builder.add_node("perform_operation", node)
    builder.add_edge(START, "perform_operation")
    builder.add_edge("perform_operation", END)
    return builder.compile(checkpointer=checkpointer)


def run_naive_scenario():
    print("\n" + "=" * 60)
    print("SCENARIO 1: Naive side effect without idempotency")
    print("=" * 60)

    external_effects = []
    node_attempts = 0

    def perform_operation(state: OperationState):
        nonlocal node_attempts
        node_attempts += 1

        operation_key = state["operation_key"]

        # Simulate a successful external operation.
        external_effects.append(operation_key)
        print(
            f"[node attempt {node_attempts}] "
            f"External effect executed: {operation_key}"
        )

        # Simulate failure after the external effect,
        # but before the node can return a state update.
        if node_attempts == 1:
            raise RuntimeError(
                "Simulated failure after external effect"
            )

        return {"status": "completed"}

    graph = build_graph(perform_operation, InMemorySaver())
    config = {
        "configurable": {
            "thread_id": "p9-d6-naive"
        }
    }


    try:
        graph.invoke(
            {
                "operation_key": "operation-001",
                "status": "pending",
            },
            config=config,
        )
    except RuntimeError as exc:
        print(f"First execution failed: {exc}")

    # Check the state immediately after the first failure.
    snapshot = graph.get_state(config)
    print("Checkpoint values after failure:", snapshot.values)
    print("Checkpoint next after failure:", snapshot.next)
    print("External effects so far:", external_effects)

    assert snapshot.next == ("perform_operation",)
    assert snapshot.values["status"] == "pending"
    assert len(external_effects) == 1

    # Resume the same thread.
    result = graph.invoke(None, config=config)

    print("Final graph result:", result)
    print("External effects after resume:", external_effects)

    assert len(external_effects) == 2
    assert external_effects == [
        "operation-001",
        "operation-001",
    ]
    assert result["status"] == "completed"

    print("PASS: Duplicate side effect reproduced.")


def run_idempotent_scenario():
    print("\n" + "=" * 60)
    print("SCENARIO 2: Simulated idempotency-key protection")
    print("=" * 60)

    external_effects = []
    processed_keys = set()
    node_attempts = 0

    def perform_external_operation(operation_key: str):
        # Simulate a deduplication check at the external
        # operation boundary.
        if operation_key in processed_keys:
            print(
                f"[external service] Duplicate key ignored: "
                f"{operation_key}"
            )
            return

        # In a real system, the deduplication record and
        # business effect must be coordinated atomically.
        processed_keys.add(operation_key)
        external_effects.append(operation_key)

        print(
            f"[external service] Effect executed: "
            f"{operation_key}"
        )

    def perform_operation(state: OperationState):
        nonlocal node_attempts
        node_attempts += 1

        operation_key = state["operation_key"]

        perform_external_operation(operation_key)

        # Again, fail after the external operation returns.
        if node_attempts == 1:
            raise RuntimeError(
                "Simulated failure after external effect"
            )

        return {"status": "completed"}

    graph = build_graph(perform_operation, InMemorySaver())
    config = {
        "configurable": {
            "thread_id": "p9-d6-idempotent"
        }
    }

    try:
        graph.invoke(
            {
                "operation_key": "operation-002",
                "status": "pending",
            },
            config=config,
        )
    except RuntimeError as exc:
        print(f"First execution failed: {exc}")

    snapshot = graph.get_state(config)
    print("Checkpoint next after failure:", snapshot.next)
    print("External effects so far:", external_effects)

    result = graph.invoke(None, config=config)

    print("Final graph result:", result)
    print("External effects after resume:", external_effects)
    print("Processed operation keys:", processed_keys)

    assert snapshot.next == ("perform_operation",)
    assert len(external_effects) == 1
    assert result["status"] == "completed"

    print("PASS: The simulated idempotency guard prevented duplication.")


if __name__ == "__main__":
    run_naive_scenario()
    run_idempotent_scenario()
