
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class ResearchState(TypedDict, total=False):
    ticker: str
    research_request: str
    research: str
    execution_count: int


def research_node(state: ResearchState) -> dict:
    ticker = state.get("ticker", "UNKNOWN")
    request = state.get("research_request", "initial")
    execution_count = state.get("execution_count", 0) + 1

    print(
        f"[research] ticker={ticker}, "
        f"request={request}, "
        f"execution_count={execution_count}"
    )

    return {
        "research": f"{ticker} research for {request}",
        "execution_count": execution_count,
    }


def build_graph():
    builder = StateGraph(ResearchState)
    builder.add_node("research", research_node)
    builder.add_edge(START, "research")
    builder.add_edge("research", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


def make_config(thread_id: str) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def inspect_thread(graph, thread_id: str) -> None:
    config = make_config(thread_id)
    snapshot = graph.get_state(config)

    print(f"\n===== Thread: {thread_id} =====")
    print("Current values:", snapshot.values)
    print("Current next:", snapshot.next)
    print(
        "Current checkpoint_id:",
        snapshot.config["configurable"].get("checkpoint_id"),
    )

    print("History:")
    for index, history_snapshot in enumerate(
        graph.get_state_history(config)
    ):
        checkpoint_id = (
            history_snapshot.config["configurable"].get("checkpoint_id")
        )

        print(
            f"  {index}: "
            f"checkpoint_id={checkpoint_id}, "
            f"next={history_snapshot.next}, "
            f"values={history_snapshot.values}"
        )


def main() -> None:
    graph = build_graph()

    thread_a = "research-session-A"
    thread_b = "research-session-B"

    config_a = make_config(thread_a)
    config_b = make_config(thread_b)

    print("\n===== 1. First execution: Thread A =====")
    result_a1 = graph.invoke(
        {
            "ticker": "AAPL",
            "research_request": "initial",
        },
        config=config_a,
    )
    print("Thread A result:", result_a1)

    print("\n===== 2. First execution: Thread B =====")
    result_b1 = graph.invoke(
        {
            "ticker": "MSFT",
            "research_request": "initial",
        },
        config=config_b,
    )
    print("Thread B result:", result_b1)

    print("\n===== 3. Continue Thread A =====")
    result_a2 = graph.invoke(
        {
            "research_request": "follow-up",
        },
        config=config_a,
    )
    print("Thread A follow-up result:", result_a2)

    print("\n===== 4. Inspect both threads =====")
    inspect_thread(graph, thread_a)
    inspect_thread(graph, thread_b)

    print("\n===== 5. Verify isolation =====")
    state_a = graph.get_state(config_a).values
    state_b = graph.get_state(config_b).values

    assert state_a["ticker"] == "AAPL"
    assert state_a["research"] == "AAPL research for follow-up"
    assert state_a["execution_count"] == 2

    assert state_b["ticker"] == "MSFT"
    assert state_b["research"] == "MSFT research for initial"
    assert state_b["execution_count"] == 1

    assert "AAPL" not in state_b["research"]
    assert "MSFT" not in state_a["research"]

    print("PASS: Thread A retains its own state.")
    print("PASS: Thread B retains its own state.")
    print("PASS: Thread A continuation did not change Thread B.")
    print("\nAll P9-D4 isolation assertions passed.")


if __name__ == "__main__":
    main()
