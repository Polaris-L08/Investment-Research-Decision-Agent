from operator import add
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph, END
from langgraph.types import Command, interrupt


class State(TypedDict):
    events: Annotated[list[str], add]


# ---------- 子图：人工审批 ----------

def approval_gate(
    state: State,
):
    print("[child] Waiting for human decision...")

    decision = interrupt({
        "question": "Approve continuing the investment research?",
        "allowed_decisions": ["approve", "reject"],
    })

    print(f"[child] Received decision: {decision}")

    if decision == "approve":
        return Command(
            update={"events": ["child: approved"]},
            goto="continue_research",
            graph=Command.PARENT,
        )

    if decision == "reject":
        return Command(
            update={"events": ["child: rejected"]},
            goto="stop_research",
            graph=Command.PARENT,
        )

    raise ValueError(f"Unsupported decision: {decision}")


child_builder = StateGraph(State)
child_builder.add_node("approval_gate", approval_gate)
child_builder.add_edge(START, "approval_gate")
child_builder.add_edge("approval_gate", END)
approval_subgraph = child_builder.compile()


# ---------- 父图：根据审批结果继续或终止 ----------

def continue_research(state: State):
    print("[parent] Continuing research.")
    return {"events": ["parent: research continued"]}


def stop_research(state: State):
    print("[parent] Research stopped.")
    return {"events": ["parent: research stopped"]}


parent_builder = StateGraph(State)
parent_builder.add_node("approval_subgraph", approval_subgraph)
parent_builder.add_node("continue_research", continue_research)
parent_builder.add_node("stop_research", stop_research)

parent_builder.add_edge(START, "approval_subgraph")
parent_builder.add_edge("continue_research", END)
parent_builder.add_edge("stop_research", END)

checkpointer = InMemorySaver()
graph = parent_builder.compile(checkpointer=checkpointer)

config = {
    "configurable": {
        "thread_id": "nested-hitl-demo-001",
    }
}


def main():
    print("\n=== Step 1: Start graph ===")
    first = graph.invoke({"events": []}, config)

    interrupts = first.get("__interrupt__", ())
    if not interrupts:
        print("ERROR: Expected an interrupt, but none was returned.")
        return

    print("Interrupt payload:", interrupts[0].value)
    print("Graph paused for human approval.")

    while True:
        decision = input("Enter approve or reject: ").strip().lower()

        if decision in {"approve", "reject"}:
            break

        print("Invalid input. Please enter approve or reject.")

    print("\n=== Step 2: Resume graph ===")
    result = graph.invoke(Command(resume=decision), config)

    print("\n=== Final state ===")
    print(result)

    expected_event = (
        "parent: research continued"
        if decision == "approve"
        else "parent: research stopped"
    )

    if expected_event in result.get("events", []):
        print("\nPASS: Nested subgraph HITL experiment completed.")
    else:
        print("\nERROR: Expected parent-graph route was not observed.")


if __name__ == "__main__":
    main()