
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class State(TypedDict):
    ticker: str
    risk_level: str
    decision_path: str
    final_result: str


def risk_assessment(
    state: State,
) -> Command[Literal["manual_review", "investment_decision"]]:
    print("[risk_assessment] risk_level =", state["risk_level"])

    if state["risk_level"] == "high":
        return Command(
            update={"decision_path": "manual_review"},
            goto="manual_review",
        )

    return Command(
        update={"decision_path": "standard"},
        goto="investment_decision",
    )


def manual_review(state: State):
    print("[manual_review] ticker =", state["ticker"])
    return {
        "final_result": "sent_to_manual_review",
    }


def investment_decision(state: State):
    print("[investment_decision] ticker =", state["ticker"])
    return {
        "final_result": "standard_decision_completed",
    }


def build_graph():
    builder = StateGraph(State)

    builder.add_node("risk_assessment", risk_assessment)
    builder.add_node("manual_review", manual_review)
    builder.add_node("investment_decision", investment_decision)

    builder.add_edge(START, "risk_assessment")
    builder.add_edge("manual_review", END)
    builder.add_edge("investment_decision", END)

    # 注意：risk_assessment 不配置静态后续边。
    # 后续节点由 Command(goto=...) 动态决定。

    return builder.compile()


def run_case(graph, risk_level: str):
    print("\n" + "=" * 55)
    print("TEST risk_level =", risk_level)
    print("=" * 55)

    result = graph.invoke(
        {
            "ticker": "AAPL",
            "risk_level": risk_level,
            "decision_path": "",
            "final_result": "",
        }
    )

    print("Result:", result)

    if risk_level == "high":
        assert result["decision_path"] == "manual_review"
        assert result["final_result"] == "sent_to_manual_review"
    else:
        assert result["decision_path"] == "standard"
        assert result["final_result"] == "standard_decision_completed"

    print("PASS")


def main():
    graph = build_graph()

    run_case(graph, "high")
    run_case(graph, "low")

    print("\nPASS: Command update/goto experiments completed.")


if __name__ == "__main__":
    main()
