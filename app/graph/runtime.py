from langchain_core.runnables import RunnableConfig

from app.graph.checkpointer import create_checkpointer
from app.graph.graph import build_graph


def create_application_graph(*, checkpointer=None):
    """Create the application graph with explicitly owned persistence.

    The default runtime path uses the local SQLite checkpointer. Supplying a
    checkpointer allows tests and future deployment environments to inject a
    different persistence backend without changing the business graph.
    """
    if checkpointer is None:
        checkpointer = create_checkpointer()

    return build_graph(checkpointer=checkpointer)


def build_thread_config(thread_id: str) -> RunnableConfig:
    """Build the runtime configuration required by checkpointed execution."""
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise ValueError("thread_id must be a non-empty string")

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }