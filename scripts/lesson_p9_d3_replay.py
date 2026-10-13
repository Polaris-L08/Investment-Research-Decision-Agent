
from collections import Counter
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class DemoState(TypedDict):
    ticker: str
    research: str
    valuation: str
    report: str


# 用于观察 Python 节点函数实际执行次数
execution_counts = Counter()


def research_node(state: DemoState) -> dict:
    execution_counts["research"] += 1
    print("[execute] research")

    return {
        "research": f"Research result for {state['ticker']}"
    }


def valuation_node(state: DemoState) -> dict:
    execution_counts["valuation"] += 1
    print("[execute] valuation")

    return {
        "valuation": f"Valuation based on: {state['research']}"
    }


def report_node(state: DemoState) -> dict:
    execution_counts["report"] += 1
    print("[execute] report")

    return {
        "report": (
            f"{state['ticker']}: "
            f"{state['research']} | {state['valuation']}"
        )
    }


builder = StateGraph(DemoState)

builder.add_node("research", research_node)
builder.add_node("valuation", valuation_node)
builder.add_node("report", report_node)

builder.add_edge(START, "research")
builder.add_edge("research", "valuation")
builder.add_edge("valuation", "report")
builder.add_edge("report", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {
    "configurable": {
        "thread_id": "p9-d3-replay-demo"
    }
}


def print_history(label: str) -> list:
    history = list(graph.get_state_history(config))

    print(f"\n===== {label} =====")

    for index, snapshot in enumerate(history):
        configurable = snapshot.config["configurable"]

        print(
            f"{index}: "
            f"checkpoint_id={configurable.get('checkpoint_id')}, "
            f"next={snapshot.next}, "
            f"values={snapshot.values}"
        )

    return history


print("===== 1. Initial execution =====")

result = graph.invoke(
    {
        "ticker": "AAPL",
        "research": "",
        "valuation": "",
        "report": "",
    },
    config=config,
)

print("\nInitial result:")
print(result)

print("\nExecution counts after initial run:")
print(dict(execution_counts))

history_before = print_history("History before replay")

# 找到“下一步是 valuation”的历史快照。
# 这意味着 research 的状态更新已在该快照中保存，
# 后续待执行节点是 valuation。
target = next(
    snapshot
    for snapshot in history_before
    if snapshot.next == ("valuation",)
)

target_config = target.config

print("\n===== 2. Selected historical checkpoint =====")
print("target values:", target.values)
print("target next:", target.next)
print("target config:", target_config)

print("\n===== 3. Replay from the selected checkpoint =====")

replay_result = graph.invoke(
    None,
    config=target_config,
)

print("\nReplay result:")
print(replay_result)

print("\nExecution counts after replay:")
print(dict(execution_counts))

history_after = print_history("History after replay")

print("\n===== 4. Verify original checkpoint still exists =====")

original_checkpoint_id = target.config["configurable"]["checkpoint_id"]

original_still_exists = any(
    snapshot.config["configurable"].get("checkpoint_id")
    == original_checkpoint_id
    for snapshot in history_after
)

print("Original checkpoint ID:", original_checkpoint_id)
print("Original checkpoint still in history:", original_still_exists)
