"""Policy-enforced application service for writing long-term memories."""

from __future__ import annotations

from dataclasses import dataclass

from app.memory.models import MemoryCandidate, MemoryItem
from app.memory.policy import MemoryWritePolicy, WriteDecision, WritePolicyResult
from app.memory.sqlite_repository import SQLiteMemoryRepository


@dataclass(frozen=True, slots=True)
class MemoryWriteResult:
    decision: WriteDecision
    reason: str
    item: MemoryItem | None = None


class MemoryService:
    def __init__(
        self,
        repository: SQLiteMemoryRepository,
        policy: MemoryWritePolicy | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or MemoryWritePolicy()

    def write(self, candidate: MemoryCandidate) -> MemoryWriteResult:
        result: WritePolicyResult = self.policy.evaluate(candidate)
        if result.decision != WriteDecision.WRITE:
            return MemoryWriteResult(result.decision, result.reason)

        # Exact duplicate suppression is scope-local and type-specific.
        normalized = " ".join(candidate.content.casefold().split())
        for existing in self.repository.list_active(
            owner_id=candidate.owner_id,
            namespace=candidate.namespace,
            memory_type=candidate.memory_type,
        ):
            if " ".join(existing.content.casefold().split()) == normalized:
                return MemoryWriteResult(
                    WriteDecision.SKIP_DUPLICATE,
                    "An equivalent active memory already exists in this scope.",
                    existing,
                )

        item = MemoryItem.from_candidate(candidate)
        stored = self.repository.create(item)
        return MemoryWriteResult(WriteDecision.WRITE, result.reason, stored)
