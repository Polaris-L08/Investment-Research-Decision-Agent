"""Deterministic write policy for long-term memory candidates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.memory.models import MemoryCandidate, MemorySourceType, MemoryType


class WriteDecision(StrEnum):
    WRITE = "write"
    REJECT = "reject"
    REQUIRE_CONFIRMATION = "require_confirmation"
    SKIP_DUPLICATE = "skip_duplicate"


@dataclass(frozen=True, slots=True)
class WritePolicyResult:
    decision: WriteDecision
    reason: str


_PREFERENCE_TYPES = {
    MemoryType.USER_PREFERENCE,
    MemoryType.WORKFLOW_PREFERENCE,
    MemoryType.CONTEXTUAL_NOTE,
}
_HISTORICAL_TYPES = {
    MemoryType.RESEARCH_HISTORY,
    MemoryType.HISTORICAL_FINDING,
}


class MemoryWritePolicy:
    """Fail-closed policy. An LLM may propose a candidate but cannot bypass it."""

    def evaluate(self, candidate: MemoryCandidate) -> WritePolicyResult:
        if candidate.contains_sensitive_data:
            return WritePolicyResult(
                WriteDecision.REJECT,
                "Sensitive data is not accepted by the ordinary long-term memory path.",
            )

        if candidate.source_type == MemorySourceType.AGENT_INFERENCE:
            return WritePolicyResult(
                WriteDecision.REQUIRE_CONFIRMATION,
                "Agent inference must not be promoted to a user preference without confirmation.",
            )

        if candidate.memory_type in _PREFERENCE_TYPES:
            if candidate.source_type == MemorySourceType.EXPLICIT_USER_STATEMENT:
                if candidate.explicit_durable_intent:
                    return WritePolicyResult(
                        WriteDecision.WRITE,
                        "Explicit durable user preference or workflow instruction.",
                    )
                return WritePolicyResult(
                    WriteDecision.REJECT,
                    "No explicit intent to retain this information across tasks.",
                )
            if candidate.source_type == MemorySourceType.USER_FEEDBACK:
                return WritePolicyResult(
                    WriteDecision.REQUIRE_CONFIRMATION,
                    "Feedback may imply a preference; confirm before retaining it as durable memory.",
                )
            return WritePolicyResult(
                WriteDecision.REJECT,
                "Preference memory requires an explicit user statement or confirmed feedback.",
            )

        if candidate.memory_type in _HISTORICAL_TYPES:
            if candidate.source_type not in {
                MemorySourceType.RESEARCH_RESULT,
                MemorySourceType.EXTERNAL_SOURCE,
                MemorySourceType.EXPLICIT_USER_STATEMENT,
            }:
                return WritePolicyResult(
                    WriteDecision.REJECT,
                    "Historical findings require a research result or attributable source.",
                )
            if not candidate.source_reference:
                return WritePolicyResult(
                    WriteDecision.REJECT,
                    "Historical findings require a source reference.",
                )
            if candidate.observed_at is None:
                return WritePolicyResult(
                    WriteDecision.REJECT,
                    "Historical findings require an observed_at timestamp.",
                )
            return WritePolicyResult(
                WriteDecision.WRITE,
                "Historical finding has provenance and an observation timestamp.",
            )

        return WritePolicyResult(
            WriteDecision.REJECT,
            "Candidate type or source is not permitted by the memory write policy.",
        )
