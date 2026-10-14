from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.memory import (
    MemoryCandidate,
    MemorySourceType,
    MemoryType,
    MemoryWritePolicy,
    WriteDecision,
)


def candidate(**overrides):
    values = {
        "memory_type": MemoryType.USER_PREFERENCE,
        "content": "Prefer free cash flow and downside valuation risk",
        "namespace": "investment_agent",
        "owner_id": "user_a",
        "source_type": MemorySourceType.EXPLICIT_USER_STATEMENT,
        "explicit_durable_intent": True,
    }
    values.update(overrides)
    return MemoryCandidate(**values)


def test_schema_rejects_blank_content():
    with pytest.raises(ValidationError):
        candidate(content="   ")


def test_schema_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        candidate(observed_at=datetime(2026, 1, 1))


def test_schema_rejects_invalid_validity_window():
    with pytest.raises(ValidationError):
        candidate(
            valid_from=datetime(2026, 1, 2, tzinfo=timezone.utc),
            valid_until=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_explicit_durable_preference_is_writable():
    assert MemoryWritePolicy().evaluate(candidate()).decision == WriteDecision.WRITE


def test_temporary_instruction_is_rejected():
    result = MemoryWritePolicy().evaluate(candidate(explicit_durable_intent=False))
    assert result.decision == WriteDecision.REJECT


def test_agent_inference_requires_confirmation():
    result = MemoryWritePolicy().evaluate(
        candidate(source_type=MemorySourceType.AGENT_INFERENCE)
    )
    assert result.decision == WriteDecision.REQUIRE_CONFIRMATION


def test_sensitive_candidate_is_rejected():
    result = MemoryWritePolicy().evaluate(candidate(contains_sensitive_data=True))
    assert result.decision == WriteDecision.REJECT


def test_historical_finding_requires_source_and_timestamp():
    item = candidate(
        memory_type=MemoryType.HISTORICAL_FINDING,
        source_type=MemorySourceType.RESEARCH_RESULT,
        source_reference="https://example.test/report",
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        explicit_durable_intent=False,
    )
    assert MemoryWritePolicy().evaluate(item).decision == WriteDecision.WRITE


def test_historical_finding_without_source_is_rejected():
    item = candidate(
        memory_type=MemoryType.HISTORICAL_FINDING,
        source_type=MemorySourceType.RESEARCH_RESULT,
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        explicit_durable_intent=False,
    )
    assert MemoryWritePolicy().evaluate(item).decision == WriteDecision.REJECT
