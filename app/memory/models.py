"""Typed models for long-term memory items and write candidates."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryType(StrEnum):
    USER_PREFERENCE = "user_preference"
    RESEARCH_HISTORY = "research_history"
    HISTORICAL_FINDING = "historical_finding"
    WORKFLOW_PREFERENCE = "workflow_preference"
    CONTEXTUAL_NOTE = "contextual_note"


class MemorySourceType(StrEnum):
    EXPLICIT_USER_STATEMENT = "explicit_user_statement"
    USER_FEEDBACK = "user_feedback"
    AGENT_INFERENCE = "agent_inference"
    RESEARCH_RESULT = "research_result"
    EXTERNAL_SOURCE = "external_source"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MemoryCandidate(BaseModel):
    """Untrusted proposed memory. It must pass MemoryWritePolicy before storage."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=20_000)
    namespace: str = Field(min_length=1, max_length=200)
    owner_id: str = Field(min_length=1, max_length=200)
    source_type: MemorySourceType
    source_reference: str | None = Field(default=None, max_length=2_000)
    summary: str | None = Field(default=None, max_length=2_000)
    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    explicit_durable_intent: bool = False
    contains_sensitive_data: bool = False

    @field_validator("content", "namespace", "owner_id")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @field_validator("observed_at", "valid_from", "valid_until")
    @classmethod
    def require_timezone_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_validity_window(self) -> "MemoryCandidate":
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be later than valid_from")
        return self


class MemoryItem(BaseModel):
    """Persistable memory record with provenance, scope, and lifecycle metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    memory_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=200)
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=20_000)
    summary: str | None = Field(default=None, max_length=2_000)
    source_type: MemorySourceType
    source_reference: str | None = Field(default=None, max_length=2_000)
    namespace: str = Field(min_length=1, max_length=200)
    owner_id: str = Field(min_length=1, max_length=200)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    version: int = Field(default=1, ge=1)
    supersedes_memory_id: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content", "namespace", "owner_id", "memory_id")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @field_validator("created_at", "updated_at", "observed_at", "valid_from", "valid_until")
    @classmethod
    def require_timezone_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_temporal_fields(self) -> "MemoryItem":
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be later than valid_from")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        if self.supersedes_memory_id == self.memory_id:
            raise ValueError("a memory cannot supersede itself")
        return self

    @classmethod
    def from_candidate(cls, candidate: MemoryCandidate) -> "MemoryItem":
        return cls(
            memory_type=candidate.memory_type,
            content=candidate.content,
            summary=candidate.summary,
            source_type=candidate.source_type,
            source_reference=candidate.source_reference,
            namespace=candidate.namespace,
            owner_id=candidate.owner_id,
            observed_at=candidate.observed_at,
            valid_from=candidate.valid_from,
            valid_until=candidate.valid_until,
            metadata=candidate.metadata,
        )
