from datetime import datetime, timedelta, timezone

import pytest

from app.memory import (
    MemoryCandidate,
    MemoryNotFoundError,
    MemoryService,
    MemorySourceType,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    SQLiteMemoryRepository,
    WriteDecision,
)


@pytest.fixture
def repo(tmp_path):
    return SQLiteMemoryRepository(tmp_path / "memory.sqlite3")


def scope(owner="user_a", namespace="investment_agent"):
    return MemoryScope(owner_id=owner, namespace=namespace)


def preference(content="Prefer FCF and valuation downside risk", owner="user_a", namespace="investment_agent"):
    return MemoryCandidate(
        memory_type=MemoryType.USER_PREFERENCE,
        content=content,
        namespace=namespace,
        owner_id=owner,
        source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
        explicit_durable_intent=True,
    )


def test_write_persists_and_reads_across_repository_instances(tmp_path):
    db_path = tmp_path / "memory.sqlite3"
    result = MemoryService(SQLiteMemoryRepository(db_path)).write(preference(), scope=scope())
    assert result.decision == WriteDecision.WRITE
    assert result.item is not None

    second_instance = SQLiteMemoryRepository(db_path)
    loaded = second_instance.get(
        result.item.memory_id, owner_id="user_a", namespace="investment_agent"
    )
    assert loaded.content == "Prefer FCF and valuation downside risk"


def test_exact_duplicate_is_suppressed(repo):
    service = MemoryService(repo)
    first = service.write(preference("Prefer FCF and valuation downside risk"), scope=scope())
    second = service.write(preference("  PREFER FCF   AND valuation downside risk "), scope=scope())
    assert first.decision == WriteDecision.WRITE
    assert second.decision == WriteDecision.SKIP_DUPLICATE
    assert second.item.memory_id == first.item.memory_id


def test_scope_isolation_applies_to_reads_and_mutations(repo):
    item = MemoryService(repo).write(preference(), scope=scope()).item
    assert item is not None
    with pytest.raises(MemoryNotFoundError):
        repo.get(item.memory_id, owner_id="user_b", namespace="investment_agent")
    with pytest.raises(MemoryNotFoundError):
        repo.revoke(item.memory_id, owner_id="user_b", namespace="investment_agent")


def test_supersede_marks_old_version_and_returns_only_current(repo):
    old = MemoryService(repo).write(preference(), scope=scope()).item
    assert old is not None
    new = repo.supersede(
        old.memory_id,
        owner_id="user_a",
        namespace="investment_agent",
        new_content="Prioritize return on invested capital and balance-sheet risk",
        source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
    )
    assert new.version == old.version + 1
    assert new.supersedes_memory_id == old.memory_id
    assert repo.get(old.memory_id, owner_id="user_a", namespace="investment_agent").status == MemoryStatus.SUPERSEDED
    active = repo.list_active(owner_id="user_a", namespace="investment_agent")
    assert [item.memory_id for item in active] == [new.memory_id]


def test_revoke_removes_item_from_active_retrieval(repo):
    item = MemoryService(repo).write(preference(), scope=scope()).item
    assert item is not None
    revoked = repo.revoke(item.memory_id, owner_id="user_a", namespace="investment_agent")
    assert revoked.status == MemoryStatus.REVOKED
    assert repo.list_active(owner_id="user_a", namespace="investment_agent") == []


def test_expiration_excludes_and_marks_due_records(repo):
    now = datetime.now(timezone.utc)
    candidate = preference("A time-limited preference").model_copy(
        update={"valid_until": now + timedelta(hours=1)}
    )
    item = MemoryService(repo).write(candidate, scope=scope()).item
    assert item is not None
    expired_at = now + timedelta(hours=2)
    assert repo.list_active(owner_id="user_a", namespace="investment_agent", now=expired_at) == []
    assert repo.expire_due(owner_id="user_a", namespace="investment_agent", now=expired_at) == 1
    assert repo.get(item.memory_id, owner_id="user_a", namespace="investment_agent").status == MemoryStatus.EXPIRED


def test_delete_removes_entire_version_lineage(repo):
    old = MemoryService(repo).write(preference(), scope=scope()).item
    assert old is not None
    new = repo.supersede(
        old.memory_id,
        owner_id="user_a",
        namespace="investment_agent",
        new_content="A revised durable preference",
    )
    deleted_count = repo.delete(
        new.memory_id, owner_id="user_a", namespace="investment_agent"
    )
    assert deleted_count == 2
    with pytest.raises(MemoryNotFoundError):
        repo.get(old.memory_id, owner_id="user_a", namespace="investment_agent")
    with pytest.raises(MemoryNotFoundError):
        repo.get(new.memory_id, owner_id="user_a", namespace="investment_agent")


def test_scope_isolation_applies_to_namespace_and_owner(repo):
    service = MemoryService(repo)
    item = service.write(preference(), scope=scope()).item
    assert item is not None

    # A known memory_id must not bypass either boundary dimension.
    with pytest.raises(MemoryNotFoundError):
        service.get(item.memory_id, scope=scope(owner="user_a", namespace="other_agent"))
    with pytest.raises(MemoryNotFoundError):
        service.get(item.memory_id, scope=scope(owner="user_b", namespace="investment_agent"))

    assert service.list_active(scope=scope(owner="user_a", namespace="other_agent")) == []
    assert service.list_active(scope=scope(owner="user_b", namespace="investment_agent")) == []


def test_service_rejects_candidate_scope_forgery(repo):
    service = MemoryService(repo)
    forged = preference(owner="user_b", namespace="investment_agent")

    result = service.write(forged, scope=scope(owner="user_a", namespace="investment_agent"))

    assert result.decision == WriteDecision.REJECT
    assert result.item is None
    assert service.list_active(scope=scope(owner="user_a", namespace="investment_agent")) == []
    assert service.list_active(scope=scope(owner="user_b", namespace="investment_agent")) == []


def test_scope_isolation_applies_to_mutations(repo):
    service = MemoryService(repo)
    item = service.write(preference(), scope=scope()).item
    assert item is not None

    foreign_scope = scope(owner="user_b", namespace="investment_agent")
    with pytest.raises(MemoryNotFoundError):
        service.supersede(item.memory_id, scope=foreign_scope, new_content="Hijacked")
    with pytest.raises(MemoryNotFoundError):
        service.revoke(item.memory_id, scope=foreign_scope)
    with pytest.raises(MemoryNotFoundError):
        service.delete(item.memory_id, scope=foreign_scope)

    assert service.get(item.memory_id, scope=scope()).status == MemoryStatus.ACTIVE


def test_memory_scope_is_immutable_and_rejects_blank_values():
    from pydantic import ValidationError

    trusted_scope = scope()
    with pytest.raises(ValidationError):
        trusted_scope.owner_id = "user_b"
    with pytest.raises(ValidationError):
        MemoryScope(owner_id="  ", namespace="investment_agent")


def test_namespace_boundary_blocks_all_mutations(repo):
    service = MemoryService(repo)
    item = service.write(preference(), scope=scope()).item
    assert item is not None
    other_namespace = scope(owner="user_a", namespace="reporting_agent")

    with pytest.raises(MemoryNotFoundError):
        service.supersede(item.memory_id, scope=other_namespace, new_content="Changed")
    with pytest.raises(MemoryNotFoundError):
        service.revoke(item.memory_id, scope=other_namespace)
    with pytest.raises(MemoryNotFoundError):
        service.delete(item.memory_id, scope=other_namespace)

    assert service.get(item.memory_id, scope=scope()).content == item.content
