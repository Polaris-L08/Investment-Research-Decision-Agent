from langchain_core.runnables import RunnableConfig

from app.application.graph import build_application_graph
from app.graph.checkpointer import create_checkpointer


def create_application_graph(*, checkpointer=None):
    """Create the production Application Graph with explicit persistence."""
    if checkpointer is None:
        checkpointer = create_checkpointer()

    return build_application_graph(checkpointer=checkpointer)


def build_thread_config(thread_id: str) -> RunnableConfig:
    """Build the runtime configuration required for checkpointed execution."""
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("thread_id must be a non-empty string")

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }