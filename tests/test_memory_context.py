from datetime import datetime, timezone

import pytest

from app.memory.context import (
    ConservativeCharacterTokenCounter,
    MemoryContextBudget,
    MemoryContextPacker,
)
from app.memory.models import MemoryCandidate, MemoryItem, MemorySourceType, MemoryType
from app.memory.retrieval import MemorySearchHit


def make_hit(content: str, *, memory_id: str, score: float = 0.8,
             source_reference: str | None = "user-message-17") -> MemorySearchHit:
    item = MemoryItem.from_candidate(
        MemoryCandidate(
            memory_type=MemoryType.USER_PREFERENCE,
            content=content,
            namespace="investment_agent",
            owner_id="user_a",
            source_type=MemorySourceType.EXPLICIT_USER_STATEMENT,
            source_reference=source_reference,
            explicit_durable_intent=True,
            observed_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
    )
    item.memory_id = memory_id
    return MemorySearchHit(item=item, score=score, matched_terms=("fcf",))


def test_packer_respects_token_budget() -> None:
    hits = [
        make_hit("Prefer FCF and valuation downside risk.", memory_id="m1"),
        make_hit("Include catalysts and invalidation conditions.", memory_id="m2"),
    ]
    packer = MemoryContextPacker(
        token_counter=ConservativeCharacterTokenCounter(chars_per_token=3),
        budget=MemoryContextBudget(max_tokens=100, max_items=5, max_content_chars=2_000),
    )
    result = packer.pack(hits)
    assert result.estimated_tokens <= result.budget_tokens
    assert len(result.included) >= 1
    assert result.estimated_tokens == packer.token_counter.count(result.text)


def test_provenance_is_preserved_when_content_is_truncated() -> None:
    hit = make_hit(
        "FCF preference. " + ("Detailed research preference " * 100),
        memory_id="long-memory",
        source_reference="conversation:lesson-11",
    )
    packer = MemoryContextPacker(
        token_counter=ConservativeCharacterTokenCounter(chars_per_token=3),
        budget=MemoryContextBudget(max_tokens=100, max_items=2, max_content_chars=2_000),
    )
    result = packer.pack([hit])
    assert len(result.included) == 1
    assert result.included[0].content_truncated is True
    assert "Memory ID: long-memory" in result.text
    assert "Source type: explicit_user_statement" in result.text
    assert "Source reference: conversation:lesson-11" in result.text
    assert "Content: " in result.text
    assert result.estimated_tokens <= result.budget_tokens


def test_oversized_item_is_reported_as_omitted_if_metadata_cannot_fit() -> None:
    hit = make_hit("x" * 2_000, memory_id="oversized")
    packer = MemoryContextPacker(
        token_counter=ConservativeCharacterTokenCounter(chars_per_token=1),
        budget=MemoryContextBudget(max_tokens=5, max_items=3, max_content_chars=2_000),
    )
    result = packer.pack([hit])
    assert result.included == ()
    assert result.omitted_memory_ids == ("oversized",)
    assert result.text == ""
    assert result.estimated_tokens == 0


def test_max_items_is_enforced_and_excess_ids_are_reported() -> None:
    hits = [
        make_hit("FCF preference one", memory_id="m1"),
        make_hit("FCF preference two", memory_id="m2"),
        make_hit("FCF preference three", memory_id="m3"),
    ]
    packer = MemoryContextPacker(
        budget=MemoryContextBudget(max_tokens=1_000, max_items=2, max_content_chars=2_000),
    )
    result = packer.pack(hits)
    assert len(result.included) == 2
    assert result.omitted_memory_ids == ("m3",)


@pytest.mark.parametrize("kwargs", [
    {"max_tokens": 0}, {"max_items": 0}, {"max_content_chars": 0},
])
def test_invalid_budget_rejected(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        MemoryContextBudget(**kwargs)


def test_character_counter_rejects_invalid_ratio() -> None:
    with pytest.raises(ValueError):
        ConservativeCharacterTokenCounter(chars_per_token=0)
