"""Deterministic governance checks for long-term memory candidates.

This module intentionally does not attempt general semantic contradiction
 detection. Conflict detection is based on an application-supplied metadata key.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable

from app.memory.models import MemoryCandidate, MemoryItem
from app.memory.policy import WriteDecision


class GovernanceAction(StrEnum):
    ALLOW = "allow"
    SKIP_DUPLICATE = "skip_duplicate"
    REQUIRE_CONFIRMATION = "require_confirmation"
    REJECT_EXPIRED = "reject_expired"


@dataclass(frozen=True, slots=True)
class GovernanceResult:
    action: GovernanceAction
    reason: str
    existing_item: MemoryItem | None = None


def normalize_memory_content(value: str) -> str:
    """Normalize superficial case/whitespace differences, not semantic meaning."""
    return " ".join(value.casefold().split())


def normalize_conflict_key(value: object) -> str | None:
    """Normalize case and whitespace around/within pipe-delimited key parts."""
    if not isinstance(value, str):
        return None

    parts = [
        " ".join(part.casefold().split())
        for part in value.split("|")
    ]
    normalized = "|".join(parts)
    return normalized or None


class MemoryGovernance:
    """Apply expiration, duplicate, and explicit conflict checks before storage."""

    def evaluate(
        self,
        candidate: MemoryCandidate,
        existing_items: Iterable[MemoryItem],
        *,
        now: datetime | None = None,
    ) -> GovernanceResult:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")

        # An already-expired candidate should not enter the active-memory path.
        if candidate.valid_until is not None and candidate.valid_until <= now:
            return GovernanceResult(
                GovernanceAction.REJECT_EXPIRED,
                "Candidate validity has already ended; expired memories are not written as active.",
            )

        candidate_content = normalize_memory_content(candidate.content)
        candidate_key = normalize_conflict_key(candidate.metadata.get("conflict_key"))
        same_key_different_content: MemoryItem | None = None

        for existing in existing_items:
            # Scope and type are expected to be constrained by the caller's repository query;
            # keep the type check here as an additional guard against accidental misuse.
            if existing.memory_type != candidate.memory_type:
                continue

            if normalize_memory_content(existing.content) == candidate_content:
                return GovernanceResult(
                    GovernanceAction.SKIP_DUPLICATE,
                    "An equivalent active memory already exists in this scope and type.",
                    existing,
                )

            existing_key = normalize_conflict_key(existing.metadata.get("conflict_key"))
            if candidate_key is not None and existing_key == candidate_key:
                same_key_different_content = existing

        if same_key_different_content is not None:
            return GovernanceResult(
                GovernanceAction.REQUIRE_CONFIRMATION,
                "A different active memory uses the same explicit conflict_key; verify the facts or supersede the prior version before writing.",
                same_key_different_content,
            )

        return GovernanceResult(
            GovernanceAction.ALLOW,
            "No expiration, duplicate, or explicit-key conflict was detected.",
        )


def governance_to_write_decision(action: GovernanceAction) -> WriteDecision:
    """Translate governance outcomes into the service's established result contract."""
    return {
        GovernanceAction.ALLOW: WriteDecision.WRITE,
        GovernanceAction.SKIP_DUPLICATE: WriteDecision.SKIP_DUPLICATE,
        GovernanceAction.REQUIRE_CONFIRMATION: WriteDecision.REQUIRE_CONFIRMATION,
        GovernanceAction.REJECT_EXPIRED: WriteDecision.REJECT,
    }[action]
