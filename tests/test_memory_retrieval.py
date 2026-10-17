
from datetime import datetime, timedelta, timezone

import pytest

from app.memory import (
    MemoryCandidate,
    MemoryScope,
    MemoryService,
    MemorySourceType,
    MemoryType,
    SQLiteMemoryRepository,
    MemorySearchQuery,
)


@pytest.fixture
def repo(tmp_path):
    return SQLiteMemoryRepository(tmp_path / "memory.sqlite3")


def scope(owner="user_a", namespace="investment_agent"):
    return MemoryScope(owner_id=owner, namespace=namespace)


def add_preference(service, content, owner="user_a", valid_until=None):
    candidate = MemoryCandidate(
        memory_type=MemoryType.USER_PREFERENCE,
        content=content,
        namespace="investment_agent",
        owner_id=owner,
        source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
        explicit_durable_intent=True,
        valid_until=valid_until,
    )
    result = service.write(candidate, scope=scope(owner))
    assert result.item is not None
    return result.item


def test_relevant_memory_ranks_first(repo):
    service = MemoryService(repo)

    add_preference(service, "Prefer FCF and valuation downside risk")
    add_preference(service, "Prefer FCF analysis for reports")
    add_preference(service, "Prefer concise report summaries")
    add_preference(
        service,
        "For NVIDIA focus on data-center revenue and gross margin",
    )

    hits = service.search(
        MemorySearchQuery(query="FCF valuation downside risk"),
        scope=scope(),
    )

    assert hits[0].item.content == "Prefer FCF and valuation downside risk"
    assert hits[0].score > hits[-1].score


def test_type_filter(repo):
    service = MemoryService(repo)

    add_preference(service, "Prefer FCF analysis")

    candidate = MemoryCandidate(
        memory_type=MemoryType.WORKFLOW_PREFERENCE,
        content="Always include explicit invalidation conditions",
        namespace="investment_agent",
        owner_id="user_a",
        source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
        explicit_durable_intent=True,
    )
    service.write(candidate, scope=scope())

    hits = service.search(
        MemorySearchQuery(
            query="invalidation conditions",
            memory_types=frozenset({MemoryType.WORKFLOW_PREFERENCE}),
        ),
        scope=scope(),
    )

    assert len(hits) == 1
    assert hits[0].item.memory_type == MemoryType.WORKFLOW_PREFERENCE


def test_unrelated_memories_filtered(repo):
    service = MemoryService(repo)

    add_preference(service, "Prefer FCF and valuation downside risk")
    add_preference(service, "Prefer concise report summaries")

    assert (
        service.search(
            MemorySearchQuery(
                query="semiconductor export restrictions",
                min_score=0.25,
            ),
            scope=scope(),
        )
        == []
    )


def test_scope_isolation(repo):
    service = MemoryService(repo)

    add_preference(
        service,
        "User A prefers FCF analysis",
        owner="user_a",
    )
    add_preference(
        service,
        "User B prefers dividend yield analysis",
        owner="user_b",
    )

    hits = service.search(
        MemorySearchQuery(
            query="dividend yield preference",
            min_score=0.1,
        ),
        scope=scope("user_a"),
    )

    assert all(hit.item.owner_id == "user_a" for hit in hits)
    assert all(
        "dividend yield" not in hit.item.content.casefold()
        for hit in hits
    )


def test_revoked_and_expired_excluded(repo):
    service = MemoryService(repo)

    revoked = add_preference(
        service,
        "Prefer FCF and downside risk",
    )
    service.revoke(revoked.memory_id, scope=scope())

    now = datetime.now(timezone.utc)

    expired = add_preference(
        service,
        "Prefer old short-term market momentum",
        valid_until=now + timedelta(minutes=1),
    )

    hits = service.search(
        MemorySearchQuery(
            query="FCF downside risk short-term market momentum",
            as_of=now + timedelta(minutes=2),
            min_score=0.1,
        ),
        scope=scope(),
    )

    assert all(
        hit.item.memory_id not in {revoked.memory_id, expired.memory_id}
        for hit in hits
    )


def test_limit_and_deterministic_order(repo):
    service = MemoryService(repo)

    add_preference(service, "Prefer FCF valuation analysis")
    add_preference(service, "Prefer FCF valuation risk")
    add_preference(service, "Prefer FCF valuation downside")

    request = MemorySearchQuery(query="FCF valuation", limit=2)

    first_result = service.search(request, scope=scope())
    second_result = service.search(request, scope=scope())

    assert len(first_result) == 2
    assert [
        hit.item.memory_id for hit in first_result
    ] == [
        hit.item.memory_id for hit in second_result
    ]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query": "   "},
        {"query": "FCF", "limit": 0},
        {"query": "FCF", "limit": 51},
        {"query": "FCF", "min_score": -0.1},
        {"query": "FCF", "min_score": 1.1},
        {"query": "FCF", "as_of": datetime(2026, 1, 1)},
    ],
)
def test_invalid_query_rejected(kwargs):
    with pytest.raises(ValueError):
        MemorySearchQuery(**kwargs)


def test_superseded_version_is_not_retrieved_but_replacement_is(repo):
    service = MemoryService(repo)

    old = add_preference(
        service,
        "Prefer FCF and valuation downside risk",
    )

    replacement = service.supersede(
        old.memory_id,
        scope=scope(),
        new_content="Prefer dividend yield and capital preservation",
    )

    old_query_hits = service.search(
        MemorySearchQuery(
            query="FCF valuation downside risk",
            min_score=0.1,
        ),
        scope=scope(),
    )

    replacement_hits = service.search(
        MemorySearchQuery(
            query="dividend yield capital preservation",
            min_score=0.1,
        ),
        scope=scope(),
    )

    assert all(
        hit.item.memory_id != old.memory_id
        for hit in old_query_hits
    )
    assert any(
        hit.item.memory_id == replacement.memory_id
        for hit in replacement_hits
    )


def test_chinese_research_query_matches_relevant_memory(repo):
    service = MemoryService(repo)

    add_preference(
        service,
        "偏好自由现金流分析，并重点评估估值下行风险",
    )
    add_preference(
        service,
        "报告应关注短期市场情绪和交易动量",
    )

    hits = service.search(
        MemorySearchQuery(
            query="估值下行风险",
            min_score=0.2,
        ),
        scope=scope(),
    )

    assert hits
    assert (
        hits[0].item.content
        == "偏好自由现金流分析，并重点评估估值下行风险"
    )
