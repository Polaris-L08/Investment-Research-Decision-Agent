import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from typing import TypedDict


class State(TypedDict):
    value: int


def increment(state: State):
    return {
        "value": state["value"] + 1,
    }


builder = StateGraph(State)

builder.add_node("increment", increment)

builder.add_edge(START, "increment")
builder.add_edge("increment", END)

connection = sqlite3.connect(
    "restart-demo.sqlite",
    check_same_thread=False,
)

checkpointer = SqliteSaver(connection)

graph = builder.compile(
    checkpointer=checkpointer,
)

config = {
    "configurable": {
        "thread_id": "demo-thread",
    }
}

snapshot = graph.get_state(config)

print(snapshot.values)

connection.close()