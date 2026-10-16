from datetime import datetime, timezone

from app.memory.context import MemoryContextBudget, MemoryContextPacker
from app.memory.models import MemoryCandidate, MemorySourceType, MemoryType
from app.memory.policy import WriteDecision
from app.memory.retrieval import MemorySearchQuery
from app.memory.scope import MemoryScope
from app.memory.service import MemoryService
from app.memory.sqlite_repository import SQLiteMemoryRepository
from app.memory.workflow import MEMORY_CONTEXT_INSTRUCTION, make_memory_context_node


def build_service(tmp_path):
    repository = SQLiteMemoryRepository(str(tmp_path / "memory.db"))
    service = MemoryService(repository)
    return service


def add_preference(service, scope, content):
    result = service.write(
        MemoryCandidate(
            memory_type=MemoryType.USER_PREFERENCE,
            content=content,
            namespace=scope.namespace,
            owner_id=scope.owner_id,
            source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
            source_reference="test:user-statement",
            observed_at=datetime.now(timezone.utc),
            explicit_durable_intent=True,
        ),
        scope=scope,
    )
    assert result.decision == WriteDecision.WRITE


def test_node_loads_relevant_memory_with_trusted_runtime_scope(tmp_path):
    service = build_service(tmp_path)
    scope = MemoryScope(owner_id="user_a", namespace="investment_agent")
    add_preference(service, scope, "For ACME valuation, include downside risk and catalysts.")

    node = make_memory_context_node(service)
    result = node(
        {"ticker": "ACME", "user_query": "Prepare a valuation with downside risks"},
        {"configurable": {"memory_owner_id": "user_a", "memory_namespace": "investment_agent"}},
    )

    assert "Memory ID:" in result["memory_context"]
    assert "downside risk" in result["memory_context"]
    assert result["memory_context_memory_ids"]
    assert MEMORY_CONTEXT_INSTRUCTION in result["memory_context"]
    assert result["memory_context_error"] == ""


def test_node_does_not_read_memory_without_trusted_scope(tmp_path):
    service = build_service(tmp_path)
    scope = MemoryScope(owner_id="user_a", namespace="investment_agent")
    add_preference(service, scope, "ACME valuation downside risk")
    node = make_memory_context_node(service)

    result = node(
        {"ticker": "ACME", "user_query": "valuation downside risk"},
        {"configurable": {"memory_owner_id": "user_b", "memory_namespace": "investment_agent"}},
    )

    assert result["memory_context"] == ""
    assert result["memory_context_memory_ids"] == []


def test_node_is_safe_noop_when_memory_service_is_not_configured():
    node = make_memory_context_node(None)
    result = node({"ticker": "ACME", "user_query": "research"}, {})
    assert result == {
        "memory_context": "",
        "memory_context_memory_ids": [],
        "memory_context_error": "",
    }


def test_node_reports_failure_without_leaking_partial_memory_context(tmp_path, monkeypatch):
    service = build_service(tmp_path)
    def broken_search(query, *, scope):
        raise RuntimeError("simulated repository failure")
    monkeypatch.setattr(service, "search", broken_search)
    node = make_memory_context_node(service)

    result = node(
        {"ticker": "ACME", "user_query": "valuation"},
        {"configurable": {"memory_owner_id": "user_a", "memory_namespace": "investment_agent"}},
    )

    assert result["memory_context"] == ""
    assert result["memory_context_memory_ids"] == []
    assert "simulated repository failure" in result["memory_context_error"]
