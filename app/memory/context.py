"""Budget-aware assembly of retrieved long-term memories into prompt context."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Protocol, Sequence

from app.memory.models import MemoryItem
from app.memory.retrieval import MemorySearchHit


class TokenCounter(Protocol):
    """Counts tokens for a specific text representation."""

    def count(self, text: str) -> int: ...


@dataclass(frozen=True, slots=True)
class ConservativeCharacterTokenCounter:
    """Dependency-free estimate, not an exact model tokenizer."""

    chars_per_token: int = 3

    def __post_init__(self) -> None:
        if self.chars_per_token < 1:
            raise ValueError("chars_per_token must be >= 1")

    def count(self, text: str) -> int:
        return ceil(len(text) / self.chars_per_token) if text else 0


@dataclass(frozen=True, slots=True)
class MemoryContextBudget:
    max_tokens: int = 1_000
    max_items: int = 5
    max_content_chars: int = 2_000

    def __post_init__(self) -> None:
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if self.max_items < 1:
            raise ValueError("max_items must be >= 1")
        if self.max_content_chars < 1:
            raise ValueError("max_content_chars must be >= 1")


@dataclass(frozen=True, slots=True)
class PackedMemory:
    hit: MemorySearchHit
    content_truncated: bool


@dataclass(frozen=True, slots=True)
class MemoryContext:
    text: str
    included: tuple[PackedMemory, ...]
    omitted_memory_ids: tuple[str, ...]
    estimated_tokens: int
    budget_tokens: int

    @property
    def is_empty(self) -> bool:
        return not self.included


class MemoryContextPacker:
    """Pack ranked, already-authorized hits under a strict context budget."""

    def __init__(
        self,
        *,
        token_counter: TokenCounter | None = None,
        budget: MemoryContextBudget | None = None,
    ) -> None:
        self.token_counter = token_counter or ConservativeCharacterTokenCounter()
        self.budget = budget or MemoryContextBudget()

    def pack(self, hits: Sequence[MemorySearchHit]) -> MemoryContext:
        selected: list[PackedMemory] = []
        omitted: list[str] = []
        blocks: list[str] = []

        for hit in hits:
            if len(selected) >= self.budget.max_items:
                omitted.append(hit.item.memory_id)
                continue

            content = hit.item.content[: self.budget.max_content_chars]
            char_truncated = len(hit.item.content) > len(content)
            block = self._render(hit, content, char_truncated)
            if self.token_counter.count(
                    self._join([*blocks, block])
            ) <= self.budget.max_tokens:
                selected.append(PackedMemory(hit, char_truncated))
                blocks.append(block)
                continue

            shortened = self._fit_shortened_content(hit, blocks, content)
            if shortened is None:
                omitted.append(hit.item.memory_id)
                continue

            shortened_block = shortened
            selected.append(PackedMemory(hit, True))
            blocks.append(shortened_block)

        text = self._join(blocks)
        estimated = self.token_counter.count(text)
        if estimated > self.budget.max_tokens:
            raise RuntimeError("packed memory context exceeds its configured budget")
        return MemoryContext(
            text=text,
            included=tuple(selected),
            omitted_memory_ids=tuple(omitted),
            estimated_tokens=estimated,
            budget_tokens=self.budget.max_tokens,
        )

    def _fit_shortened_content(
        self,
        hit: MemorySearchHit,
        existing_blocks: list[str],
        original_content: str,
    ) -> str | None:
        marker = "…[content truncated]"
        low, high = 0, len(original_content)
        best: str | None = None
        while low <= high:
            middle = (low + high) // 2
            block = self._render(hit, original_content[:middle] + marker, True)
            candidate = self._join([*existing_blocks, block])
            if self.token_counter.count(candidate) <= self.budget.max_tokens:
                best = block
                low = middle + 1
            else:
                high = middle - 1
        return best

    @staticmethod
    def _join(blocks: Sequence[str]) -> str:
        return "\n\n".join(blocks)

    @staticmethod
    def _render(hit: MemorySearchHit, content: str, truncated: bool) -> str:
        item: MemoryItem = hit.item
        lines = [
            f"[Memory type: {item.memory_type.value}]",
            f"Memory ID: {item.memory_id}",
            f"Source type: {item.source_type.value}",
        ]
        if item.source_reference:
            lines.append(f"Source reference: {item.source_reference}")
        if item.observed_at is not None:
            lines.append(f"Observed at: {item.observed_at.isoformat()}")
        if item.valid_from is not None:
            lines.append(f"Valid from: {item.valid_from.isoformat()}")
        if item.valid_until is not None:
            lines.append(f"Valid until: {item.valid_until.isoformat()}")
        if item.summary:
            lines.append(f"Summary: {item.summary}")
        lines.append(f"Content: {content}")
        if truncated and "…[content truncated]" not in content:
            lines.append("Content note: content shortened to fit the memory context budget.")
        return "\n".join(lines)
