"""Policy-enforced application service for writing long-term memories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.memory.models import MemoryCandidate, MemoryItem, MemoryType
from app.memory.policy import MemoryWritePolicy, WriteDecision, WritePolicyResult
from app.memory.sqlite_repository import SQLiteMemoryRepository
from app.memory.scope import MemoryScope


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

    def write(
        self,
        candidate: MemoryCandidate,
        *,
        scope: MemoryScope,
    ) -> MemoryWriteResult:
        """Write only within the trusted scope supplied by the application.

        Candidate scope fields are treated as claims, not as authority. They
        must match the trusted scope exactly before the policy is evaluated.
        """
        if candidate.owner_id != scope.owner_id or candidate.namespace != scope.namespace:
            return MemoryWriteResult(
                WriteDecision.REJECT,
                "Candidate scope does not match the trusted access scope.",
            )

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

    def get(self, memory_id: str, *, scope: MemoryScope) -> MemoryItem:
        """Read a memory using a trusted scope, never an ID alone."""
        return self.repository.get(
            memory_id, owner_id=scope.owner_id, namespace=scope.namespace
        )

    def list_active(
        self,
        *,
        scope: MemoryScope,
        memory_type: MemoryType | None = None,
        now: datetime | None = None,
    ) -> list[MemoryItem]:
        return self.repository.list_active(
            owner_id=scope.owner_id,
            namespace=scope.namespace,
            memory_type=memory_type,
            now=now,
        )

    def supersede(
        self,
        memory_id: str,
        *,
        scope: MemoryScope,
        new_content: str,
        **changes,
    ) -> MemoryItem:
        return self.repository.supersede(
            memory_id,
            owner_id=scope.owner_id,
            namespace=scope.namespace,
            new_content=new_content,
            **changes,
        )

    def revoke(self, memory_id: str, *, scope: MemoryScope) -> MemoryItem:
        return self.repository.revoke(
            memory_id, owner_id=scope.owner_id, namespace=scope.namespace
        )

    def delete(self, memory_id: str, *, scope: MemoryScope) -> int:
        return self.repository.delete(
            memory_id, owner_id=scope.owner_id, namespace=scope.namespace
        )

    def expire_due(self, *, scope: MemoryScope, now: datetime | None = None) -> int:
        return self.repository.expire_due(
            owner_id=scope.owner_id, namespace=scope.namespace, now=now
        )
