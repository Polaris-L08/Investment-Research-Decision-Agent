"""Policy-enforced application service for writing long-term memories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.memory.governance import MemoryGovernance, GovernanceAction, governance_to_write_decision
from app.memory.models import MemoryCandidate, MemoryItem, MemoryType
from app.memory.policy import MemoryWritePolicy, WriteDecision, WritePolicyResult
from app.memory.retrieval import MemoryRetriever, MemorySearchQuery, MemorySearchHit
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
        retriever: MemoryRetriever | None = None,
        governance: MemoryGovernance | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or MemoryWritePolicy()
        self.retriever = retriever or MemoryRetriever()
        self.governance = governance or MemoryGovernance()

    def write(
        self,
        candidate: MemoryCandidate,
        *,
        scope: MemoryScope,
    ) -> MemoryWriteResult:
        """Write within trusted scope after policy and governance checks.

        The order is deliberate: scope validation -> write policy -> governance
        -> persistence. A candidate's own scope fields never grant authority.
        """
        if candidate.owner_id != scope.owner_id or candidate.namespace != scope.namespace:
            return MemoryWriteResult(
                WriteDecision.REJECT,
                "Candidate scope does not match the trusted access scope.",
            )

        policy_result: WritePolicyResult = self.policy.evaluate(candidate)
        if policy_result.decision != WriteDecision.WRITE:
            return MemoryWriteResult(policy_result.decision, policy_result.reason)

        now = datetime.now(timezone.utc)
        existing_items = self.repository.list_active(
            owner_id=scope.owner_id,
            namespace=scope.namespace,
            memory_type=candidate.memory_type,
            now=now,
        )
        governance_result = self.governance.evaluate(candidate, existing_items, now=now)
        if governance_result.action != GovernanceAction.ALLOW:
            return MemoryWriteResult(
                governance_to_write_decision(governance_result.action),
                governance_result.reason,
                governance_result.existing_item,
            )

        item = MemoryItem.from_candidate(candidate)
        stored = self.repository.create(item)
        return MemoryWriteResult(WriteDecision.WRITE, policy_result.reason, stored)

    def get(self, memory_id: str, *, scope: MemoryScope) -> MemoryItem:
        """Read a memory using a trusted scope, never an ID alone."""
        return self.repository.get(
            memory_id, owner_id=scope.owner_id, namespace=scope.namespace
        )

    def list_active(self, *, scope: MemoryScope, memory_type: MemoryType | None = None, now: datetime | None = None,
    ) -> list[MemoryItem]:
        return self.repository.list_active(
            owner_id=scope.owner_id,
            namespace=scope.namespace,
            memory_type=memory_type,
            now=now,
        )

    def search(self, query: MemorySearchQuery, *, scope: MemoryScope) -> list[MemorySearchHit]:
        items = self.repository.list_active(owner_id=scope.owner_id, namespace=scope.namespace, now=query.as_of)
        return self.retriever.search(items,query)

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
