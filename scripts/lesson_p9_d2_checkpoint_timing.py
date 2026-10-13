from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class DemoState(TypedDict):
    value: int
    status: str


# 模拟外部副作用：统计节点实际执行次数
execution_counts = {
    "node_a": 0,
    "node_b": 0,
}

# 第一次执行时，让 node_b 失败
should_fail = True


def node_a(state: DemoState) -> dict:
    execution_counts["node_a"] += 1

    print("[node_a] executing")

    return {
        "value": state["value"] + 1,
        "status": "node_a_completed",
    }


def node_b(state: DemoState) -> dict:
    global should_fail

    execution_counts["node_b"] += 1

    print("[node_b] executing")

    if should_fail:
        raise RuntimeError("simulated node_b failure")

    return {
        "value": state["value"] + 10,
        "status": "node_b_completed",
    }


builder = StateGraph(DemoState)

builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)

builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": "p9-d2-demo"
    }
}


def print_snapshot(label: str) -> None:
    snapshot = graph.get_state(config)

    print(f"\n===== {label} =====")
    print("values:", snapshot.values)
    print("next:", snapshot.next)
    print("metadata:", snapshot.metadata)
    print("config:", snapshot.config)

    print("\nCheckpoint history:")

    for index, item in enumerate(graph.get_state_history(config)):
        configurable = item.config.get("configurable", {})

        print(
            index,
            "checkpoint_id=",
            configurable.get("checkpoint_id"),
            "next=",
            item.next,
            "values=",
            item.values,
        )


print("===== First invocation: expected failure =====")

try:
    graph.invoke(
        {
            "value": 0,
            "status": "started",
        },
        config=config,
    )
except RuntimeError as exc:
    print("Caught error:", exc)

print_snapshot("After failure")

print("\nExecution counts:", execution_counts)

print("\n===== Resume after fixing the simulated failure =====")

should_fail = False

result = graph.invoke(None, config=config)

print("Final result:", result)
print("Execution counts:", execution_counts)

print_snapshot("After successful completion")