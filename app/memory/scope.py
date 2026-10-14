"""Trusted scope contract for long-term memory operations.

A MemoryScope must be built by the application layer from authenticated/session
context. It must never be populated directly from LLM output or an untrusted
request body without authorization checks.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryScope(BaseModel):
    """The smallest supported access boundary: owner + namespace."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    owner_id: str = Field(min_length=1, max_length=200)
    namespace: str = Field(min_length=1, max_length=200)

    @field_validator("owner_id", "namespace")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("scope values must not be blank")
        return value.strip()
