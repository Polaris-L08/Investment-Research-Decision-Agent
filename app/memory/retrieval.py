"""Deterministic lexical retrieval for scope-filtered long-term memories."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from app.memory.models import MemoryItem, MemoryType

_STOPWORDS = {"a","an","and","are","as","at","be","by","for","from","how","i","in","is","it","me","my","of","on","or","our","please","the","this","to","we","what","when","with","you","your"}
_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)

def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())

def _tokens(text: str) -> set[str]:
    result = set()
    for token in _TOKEN_RE.findall(text.casefold()):
        if re.fullmatch(r"[a-z0-9]+", token):
            if token not in _STOPWORDS:
                result.add(token)
        elif len(token) == 1:
            result.add(token)
        else:
            result.add(token)
            result.update(token[i:i+2] for i in range(len(token)-1))
    return result

@dataclass(frozen=True, slots=True)
class MemorySearchQuery:
    query: str
    memory_types: frozenset[MemoryType] | None = None
    limit: int = 5
    min_score: float = 0.15
    as_of: datetime | None = None

    def __post_init__(self):
        if not self.query or not self.query.strip():
            raise ValueError("query must not be blank")
        if not 1 <= self.limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")
        if self.as_of is not None and self.as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")

@dataclass(frozen=True, slots=True)
class MemorySearchHit:
    item: MemoryItem
    score: float
    matched_terms: tuple[str, ...]

class MemoryRetriever:
    """Ranks only the active, already-authorized records passed by the service."""
    def search(self, items: Iterable[MemoryItem], request: MemorySearchQuery) -> list[MemorySearchHit]:
        qterms = _tokens(request.query)
        if not qterms:
            return []
        qtext = _normalize(request.query)
        hits = []
        for item in items:
            if request.memory_types is not None and item.memory_type not in request.memory_types:
                continue
            text = " ".join(part for part in (item.summary, item.content) if part)
            dterms = _tokens(text)
            overlap = qterms & dterms
            if not overlap:
                continue
            coverage = len(overlap) / len(qterms)
            jaccard = len(overlap) / len(qterms | dterms)
            phrase_bonus = 0.10 if qtext in _normalize(text) else 0.0
            score = min(1.0, 0.80 * coverage + 0.20 * jaccard + phrase_bonus)
            if score < request.min_score:
                continue
            hits.append(MemorySearchHit(item, round(score, 6), tuple(sorted(overlap))))
        def recency(hit):
            item = hit.item
            return (item.observed_at or item.updated_at or item.created_at).timestamp()
        hits.sort(key=lambda h: (-h.score, -recency(h), h.item.memory_id))
        return hits[:request.limit]
