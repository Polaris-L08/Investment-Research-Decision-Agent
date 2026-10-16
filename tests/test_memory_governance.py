from datetime import datetime, timedelta, timezone

import pytest

from app.memory import (
    MemoryCandidate,
    MemoryGovernance,
    MemoryService,
    MemorySourceType,
    MemoryScope,
    MemoryType,
    SQLiteMemoryRepository,
    WriteDecision,
)


def scope(owner="user_a", namespace="investment_agent"):
    return MemoryScope(owner_id=owner, namespace=namespace)


def preference(content, *, metadata=None, valid_until=None):
    return MemoryCandidate(
        memory_type=MemoryType.USER_PREFERENCE,
        content=content,
        namespace="investment_agent",
        owner_id="user_a",
        source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
        explicit_durable_intent=True,
        metadata=metadata or {},
        valid_until=valid_until,
    )


@pytest.fixture
def service(tmp_path):
    return MemoryService(SQLiteMemoryRepository(tmp_path / "memory.sqlite3"))


def test_duplicate_is_still_suppressed_by_governance(service):
    first = service.write(preference("Prefer concise reports"), scope=scope())
    second = service.write(preference("  PREFER   concise reports "), scope=scope())

    assert first.decision == WriteDecision.WRITE
    assert second.decision == WriteDecision.SKIP_DUPLICATE
    assert second.item is not None
    assert second.item.memory_id == first.item.memory_id


def test_candidate_whose_validity_has_ended_is_rejected(service):
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    result = service.write(preference("Temporary preference", valid_until=past), scope=scope())

    assert result.decision == WriteDecision.REJECT
    assert "validity has already ended" in result.reason
    assert service.list_active(scope=scope()) == []


def test_same_explicit_conflict_key_requires_confirmation(service):
    first = service.write(
        preference("Revenue for FY2025 is 100 million", metadata={"conflict_key": "acme|revenue|FY2025|USD"}),
        scope=scope(),
    )
    second = service.write(
        preference("Revenue for FY2025 is 120 million", metadata={"conflict_key": "acme|revenue|FY2025|USD"}),
        scope=scope(),
    )

    assert first.decision == WriteDecision.WRITE
    assert second.decision == WriteDecision.REQUIRE_CONFIRMATION
    assert second.item is not None
    assert second.item.memory_id == first.item.memory_id
    assert len(service.list_active(scope=scope())) == 1


def test_conflict_key_normalization_ignores_case_and_whitespace(service):
    first = service.write(
        preference("Revenue is 100", metadata={"conflict_key": "ACME | Revenue | FY2025"}),
        scope=scope(),
    )
    result = service.write(
        preference("Revenue is 120", metadata={"conflict_key": " acme| revenue | fy2025 "}),
        scope=scope(),
    )

    assert result.decision == WriteDecision.REQUIRE_CONFIRMATION


def test_different_conflict_keys_are_not_assumed_to_conflict(service):
    service.write(
        preference("FY2025 revenue is 100", metadata={"conflict_key": "acme|revenue|FY2025"}),
        scope=scope(),
    )
    result = service.write(
        preference("Q1 revenue is 30", metadata={"conflict_key": "acme|revenue|Q1-2025"}),
        scope=scope(),
    )

    assert result.decision == WriteDecision.WRITE
    assert len(service.list_active(scope=scope())) == 2


def test_without_explicit_conflict_key_no_semantic_conflict_is_inferred(service):
    service.write(preference("Revenue is 100"), scope=scope())
    result = service.write(preference("Revenue is 120"), scope=scope())

    assert result.decision == WriteDecision.WRITE
    assert len(service.list_active(scope=scope())) == 2


def test_governance_rejects_naive_now():
    candidate = preference("Any preference")
    with pytest.raises(ValueError, match="timezone-aware"):
        MemoryGovernance().evaluate(candidate, [], now=datetime(2026, 1, 1))


def test_governance_is_scoped_to_active_records(service):
    first = service.write(
        preference("Revenue is 100", metadata={"conflict_key": "acme|revenue|FY2025"}),
        scope=scope(),
    )
    assert first.item is not None
    service.revoke(first.item.memory_id, scope=scope())

    result = service.write(
        preference("Revenue is 120", metadata={"conflict_key": "acme|revenue|FY2025"}),
        scope=scope(),
    )
    assert result.decision == WriteDecision.WRITE
