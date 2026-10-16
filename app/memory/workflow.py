"""Read-only integration of long-term memory into the investment workflow.

Memory is retrieved using a trusted scope supplied through LangGraph's runtime
config. Retrieved memories are background context, not evidence for current
financial facts or investment conclusions.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.memory.context import MemoryContextPacker
from app.memory.retrieval import MemorySearchQuery
from app.memory.scope import MemoryScope
from app.memory.service import MemoryService

MEMORY_CONTEXT_INSTRUCTION = (
    "The following is long-term memory from prior interactions or research. "
    "Use it only as background context for personalization and research leads. "
    "It is not verified evidence for current financial facts, prices, forecasts, "
    "or investment conclusions. Re-verify factual claims using current sources. "
    "If memory conflicts with current sourced evidence, prefer the current "
    "evidence and state the discrepancy when relevant. Do not cite memory as an "
    "external source.\n\n"
)


def make_memory_context_node(
    memory_service: MemoryService | None,
    *,
    context_packer: MemoryContextPacker | None = None,
    result_limit: int = 10,
    min_score: float = 0.12,
):
    """Build a LangGraph node that retrieves scope-isolated memory context.

    Trusted scope is read only from runtime config's ``configurable`` mapping,
    never from graph state or the user's query. Missing scope or service is a
    safe no-op, preserving backward compatibility for existing callers.
    """
    if result_limit < 1:
        raise ValueError("result_limit must be >= 1")
    if not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between 0 and 1")

    packer = context_packer or MemoryContextPacker()

    def load_memory_context(state: Mapping[str, Any], config: Mapping[str, Any] | None = None) -> dict[str, Any]:
        empty = {"memory_context": "", "memory_context_memory_ids": [], "memory_context_error": ""}
        if memory_service is None:
            return empty

        configurable = (config or {}).get("configurable", {})
        if not isinstance(configurable, Mapping):
            return empty
        owner_id = configurable.get("memory_owner_id")
        namespace = configurable.get("memory_namespace")
        if not isinstance(owner_id, str) or not owner_id.strip():
            return empty
        if not isinstance(namespace, str) or not namespace.strip():
            return empty

        ticker = state.get("ticker", "")
        user_query = state.get("user_query", "")
        query_text = f"{ticker} {user_query}".strip()
        if not query_text:
            return empty

        try:
            scope = MemoryScope(owner_id=owner_id, namespace=namespace)
            hits = memory_service.search(
                MemorySearchQuery(query=query_text, limit=result_limit, min_score=min_score),
                scope=scope,
            )
            packed = packer.pack(hits)
            context = (
                MEMORY_CONTEXT_INSTRUCTION + packed.text
                if not packed.is_empty
                else ""
            )
            return {
                "memory_context": context,
                "memory_context_memory_ids": [entry.hit.item.memory_id for entry in packed.included],
                "memory_context_error": "",
            }
        except Exception as exc:
            # Memory is an optional enhancement: retrieval failure must not
            # fabricate context or silently become a research fact. Preserve a
            # diagnostic state field and let the main research workflow run.
            return {
                "memory_context": "",
                "memory_context_memory_ids": [],
                "memory_context_error": f"{type(exc).__name__}: {exc}",
            }

    return load_memory_context
