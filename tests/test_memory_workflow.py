from datetime import datetime, timezone

from app.memory.context import MemoryContextBudget, MemoryContextPacker
from app.memory.models import MemoryCandidate, MemorySourceType, MemoryType
from app.memory.policy import WriteDecision
from app.memory.retrieval import MemorySearchQuery
from app.memory.scope import MemoryScope
from app.memory.service import MemoryService
from app.memory.sqlite_repository import SQLiteMemoryRepository
from app.memory.workflow import MEMORY_CONTEXT_INSTRUCTION, make_memory_context_node, make_memory_capture_node


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

    node = make_memory_context_node(
        service,
        context_packer=MemoryContextPacker(budget=MemoryContextBudget(max_tokens=500)),
    )
    result = node(
        {"ticker": "ACME", "user_query": "Prepare a valuation with downside risks"},
        {"configurable": {"memory_owner_id": "user_a", "memory_namespace": "investment_agent"}},
    )

    assert "Memory ID:" in result["memory_context"]
    assert "downside risk" in result["memory_context"]
    assert result["memory_context_memory_ids"]
    assert MEMORY_CONTEXT_INSTRUCTION in result["memory_context"]
    assert result["memory_context_error"] == ""


def test_node_does_not_read_memory_from_another_owner(tmp_path):
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


def test_capture_writes_only_after_successful_report(tmp_path):
    service = build_service(tmp_path)
    node = make_memory_capture_node(service, history_ttl_days=30)
    state = {
        "ticker": "acme",
        "approval_status": "approved",
        "current_stage": "completed",
        "application_error": "",
        "report": object(),
        "report_markdown": "# ACME report",
    }
    config = {"configurable": {
        "memory_owner_id": "user_a",
        "memory_namespace": "investment_agent",
        "memory_source_reference": "application-run:test-001",
    }}

    result = node(state, config)

    assert result["memory_capture_decision"] == WriteDecision.WRITE.value
    assert result["memory_capture_memory_id"]
    items = service.list_active(scope=MemoryScope(owner_id="user_a", namespace="investment_agent"))
    assert len(items) == 1
    item = items[0]
    assert item.memory_type == MemoryType.RESEARCH_HISTORY
    assert item.source_type == MemorySourceType.RESEARCH_RESULT
    assert item.source_reference == "application-run:test-001"
    assert "ACME" in item.content
    assert "# ACME report" not in item.content


def test_capture_skips_failed_report_without_writing(tmp_path, monkeypatch):
    service = build_service(tmp_path)

    def should_not_write(candidate, *, scope):
        raise AssertionError("write must not be called for a failed report")

    monkeypatch.setattr(service, "write", should_not_write)
    node = make_memory_capture_node(service)
    result = node(
        {
            "ticker": "ACME", "approval_status": "approved", "current_stage": "report",
            "application_error": "report failed", "report": object(), "report_markdown": "partial",
        },
        {"configurable": {"memory_owner_id": "user_a", "memory_namespace": "investment_agent"}},
    )
    assert result["memory_capture_decision"] == "skipped"
    assert "did not complete successfully" in result["memory_capture_reason"]


def test_capture_write_failure_does_not_raise_or_change_report_status(tmp_path, monkeypatch):
    service = build_service(tmp_path)

    def broken_write(candidate, *, scope):
        raise RuntimeError("simulated disk failure")

    monkeypatch.setattr(service, "write", broken_write)
    node = make_memory_capture_node(service)
    result = node(
        {
            "ticker": "ACME", "approval_status": "approved", "current_stage": "completed",
            "application_error": "", "report": object(), "report_markdown": "# report",
        },
        {"configurable": {
            "memory_owner_id": "user_a", "memory_namespace": "investment_agent",
            "memory_source_reference": "application-run:test-002",
        }},
    )
    assert result["memory_capture_decision"] == "error"
    assert "simulated disk failure" in result["memory_capture_error"]
    assert "report is preserved" in result["memory_capture_reason"]


def test_node_is_noop_without_trusted_scope_even_if_state_contains_identity(tmp_path):
    service = build_service(tmp_path)
    scope = MemoryScope(owner_id="user_a", namespace="investment_agent")
    add_preference(service, scope, "ACME downside risk")
    node = make_memory_context_node(service)

    # An identity-shaped field in user-controlled graph state must never grant access.
    result = node(
        {
            "ticker": "ACME", "user_query": "downside risk",
            "memory_owner_id": "user_a", "memory_namespace": "investment_agent",
        },
        {"configurable": {}},
    )
    assert result["memory_context"] == ""
    assert result["memory_context_memory_ids"] == []


def test_capture_skips_when_traceable_source_reference_is_missing(tmp_path):
    service = build_service(tmp_path)
    node = make_memory_capture_node(service)
    result = node(
        {
            "ticker": "ACME", "approval_status": "approved", "current_stage": "completed",
            "application_error": "", "report": object(), "report_markdown": "# report",
        },
        {"configurable": {"memory_owner_id": "user_a", "memory_namespace": "investment_agent"}},
    )
    assert result["memory_capture_decision"] == "skipped"
    assert "memory_source_reference" in result["memory_capture_reason"]
