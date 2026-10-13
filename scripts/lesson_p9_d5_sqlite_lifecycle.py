
import sqlite3
import tempfile
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class DemoState(TypedDict, total=False):
    ticker: str
    research: str


def build_graph(checkpointer: SqliteSaver):
    builder = StateGraph(DemoState)

    def research_node(state: DemoState) -> dict:
        ticker = state["ticker"]
        print(f"[research] processing {ticker}")
        return {"research": f"Research result for {ticker}"}

    builder.add_node("research", research_node)
    builder.add_edge(START, "research")
    builder.add_edge("research", END)

    return builder.compile(checkpointer=checkpointer)


def main() -> None:
    thread_id = "p9-d5-persistence-demo"
    config = {"configurable": {"thread_id": thread_id}}

    # 使用临时目录，避免触碰正式项目的 Checkpoint 数据库。
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "checkpoints.sqlite"

        print("===== 1. Create connection A and Graph A =====")
        connection_a = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )

        try:
            checkpointer_a = SqliteSaver(connection_a)
            checkpointer_a.setup()
            graph_a = build_graph(checkpointer_a)

            result_a = graph_a.invoke(
                {"ticker": "AAPL"},
                config=config,
            )

            print("Graph A result:", result_a)

            snapshot_a = graph_a.get_state(config)
            print("Graph A saved values:", snapshot_a.values)
            print("Graph A next:", snapshot_a.next)

        finally:
            # 显式关闭本实验创建的连接。
            connection_a.close()

        print("\n===== 2. Reopen database with connection B =====")
        connection_b = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )

        try:
            checkpointer_b = SqliteSaver(connection_b)
            checkpointer_b.setup()
            graph_b = build_graph(checkpointer_b)

            snapshot_b = graph_b.get_state(config)

            print("Graph B restored values:", snapshot_b.values)
            print("Graph B next:", snapshot_b.next)
            print(
                "Restored checkpoint_id:",
                snapshot_b.config["configurable"].get(
                    "checkpoint_id"
                ),
            )

            assert snapshot_b.values["ticker"] == "AAPL"
            assert (
                snapshot_b.values["research"]
                == "Research result for AAPL"
            )
            assert snapshot_b.next == ()

            print("\nPASS: State survived connection recreation.")
            print("PASS: The completed thread was restored.")

        finally:
            connection_b.close()


if __name__ == "__main__":
    main()
