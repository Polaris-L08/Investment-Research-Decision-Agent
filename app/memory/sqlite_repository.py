"""SQLite-backed repository for long-term memory.

The repository enforces owner + namespace scoping on every read or mutation.
It is intentionally separate from LangGraph checkpoint storage: checkpoint data
restores workflow execution; this repository stores cross-thread memory items.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.memory.models import MemoryItem, MemoryStatus, MemoryType, MemorySourceType


def _dt_dump(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _dt_load(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class MemoryNotFoundError(LookupError):
    """Raised when a memory does not exist inside the supplied scope."""


class MemoryScopeError(PermissionError):
    """Raised when a mutation would cross an owner/namespace boundary."""


class SQLiteMemoryRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    source_type TEXT NOT NULL,
                    source_reference TEXT,
                    namespace TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    observed_at TEXT,
                    valid_from TEXT,
                    valid_until TEXT,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK(version >= 1),
                    supersedes_memory_id TEXT,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_memories_scope_status "
                "ON memories(owner_id, namespace, status, memory_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_memories_supersedes "
                "ON memories(supersedes_memory_id)"
            )

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            memory_id=row["memory_id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            summary=row["summary"],
            source_type=MemorySourceType(row["source_type"]),
            source_reference=row["source_reference"],
            namespace=row["namespace"],
            owner_id=row["owner_id"],
            created_at=_dt_load(row["created_at"]),
            updated_at=_dt_load(row["updated_at"]),
            observed_at=_dt_load(row["observed_at"]),
            valid_from=_dt_load(row["valid_from"]),
            valid_until=_dt_load(row["valid_until"]),
            status=MemoryStatus(row["status"]),
            version=row["version"],
            supersedes_memory_id=row["supersedes_memory_id"],
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _insert(conn: sqlite3.Connection, item: MemoryItem) -> None:
        conn.execute(
            """
            INSERT INTO memories (
                memory_id, memory_type, content, summary, source_type,
                source_reference, namespace, owner_id, created_at, updated_at,
                observed_at, valid_from, valid_until, status, version,
                supersedes_memory_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.memory_id, item.memory_type.value, item.content, item.summary,
                item.source_type.value, item.source_reference, item.namespace,
                item.owner_id, _dt_dump(item.created_at), _dt_dump(item.updated_at),
                _dt_dump(item.observed_at), _dt_dump(item.valid_from),
                _dt_dump(item.valid_until), item.status.value, item.version,
                item.supersedes_memory_id,
                json.dumps(item.metadata, ensure_ascii=False, default=str),
            ),
        )

    def create(self, item: MemoryItem) -> MemoryItem:
        if item.status != MemoryStatus.ACTIVE:
            raise ValueError("new memory must start in active status")
        with self._connect() as conn:
            if item.supersedes_memory_id is not None:
                parent = conn.execute(
                    "SELECT * FROM memories WHERE memory_id = ? AND owner_id = ? AND namespace = ?",
                    (item.supersedes_memory_id, item.owner_id, item.namespace),
                ).fetchone()
                if parent is None:
                    raise MemoryNotFoundError("superseded memory not found in this scope")
                if parent["status"] != MemoryStatus.ACTIVE.value:
                    raise ValueError("only an active memory can be superseded")
                if item.version != parent["version"] + 1:
                    raise ValueError("new version must increment the prior version by one")
                conn.execute(
                    "UPDATE memories SET status = ?, updated_at = ? WHERE memory_id = ?",
                    (MemoryStatus.SUPERSEDED.value, _dt_dump(datetime.now(timezone.utc)), item.supersedes_memory_id),
                )
            self._insert(conn, item)
        return item

    def get(self, memory_id: str, *, owner_id: str, namespace: str) -> MemoryItem:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE memory_id = ? AND owner_id = ? AND namespace = ?",
                (memory_id, owner_id, namespace),
            ).fetchone()
        if row is None:
            # Same error for missing and out-of-scope records prevents ID probing.
            raise MemoryNotFoundError("memory not found in this scope")
        return self._row_to_item(row)

    def list_active(
        self,
        *,
        owner_id: str,
        namespace: str,
        memory_type: MemoryType | None = None,
        now: datetime | None = None,
    ) -> list[MemoryItem]:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        now_iso = _dt_dump(now)
        query = (
            "SELECT * FROM memories WHERE owner_id = ? AND namespace = ? "
            "AND status = ? AND (valid_from IS NULL OR valid_from <= ?) "
            "AND (valid_until IS NULL OR valid_until > ?)"
        )
        params: list[Any] = [owner_id, namespace, MemoryStatus.ACTIVE.value, now_iso, now_iso]
        if memory_type is not None:
            query += " AND memory_type = ?"
            params.append(memory_type.value)
        query += " ORDER BY created_at DESC, memory_id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_item(row) for row in rows]

    def supersede(
        self,
        memory_id: str,
        *,
        owner_id: str,
        namespace: str,
        new_content: str,
        source_type: MemorySourceType | None = None,
        source_reference: str | None = None,
        observed_at: datetime | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem:
        old = self.get(memory_id, owner_id=owner_id, namespace=namespace)
        if old.status != MemoryStatus.ACTIVE:
            raise ValueError("only an active memory can be superseded")
        now = datetime.now(timezone.utc)
        new_item = old.model_copy(
            update={
                "memory_id": str(uuid4()),
                "content": new_content.strip(),
                "summary": summary if summary is not None else old.summary,
                "source_type": source_type or old.source_type,
                "source_reference": source_reference if source_reference is not None else old.source_reference,
                "created_at": now,
                "updated_at": now,
                "observed_at": observed_at if observed_at is not None else old.observed_at,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "status": MemoryStatus.ACTIVE,
                "version": old.version + 1,
                "supersedes_memory_id": old.memory_id,
                "metadata": metadata if metadata is not None else old.metadata,
            }
        )
        # Re-validate updated fields instead of trusting model_copy(update=...).
        new_item = MemoryItem.model_validate(new_item.model_dump())
        return self.create(new_item)

    def revoke(self, memory_id: str, *, owner_id: str, namespace: str) -> MemoryItem:
        item = self.get(memory_id, owner_id=owner_id, namespace=namespace)
        if item.status != MemoryStatus.ACTIVE:
            return item
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                "UPDATE memories SET status = ?, updated_at = ? WHERE memory_id = ? AND owner_id = ? AND namespace = ?",
                (MemoryStatus.REVOKED.value, _dt_dump(now), memory_id, owner_id, namespace),
            )
        return self.get(memory_id, owner_id=owner_id, namespace=namespace)

    def expire_due(self, *, owner_id: str, namespace: str, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE memories SET status = ?, updated_at = ? "
                "WHERE owner_id = ? AND namespace = ? AND status = ? AND valid_until IS NOT NULL AND valid_until <= ?",
                (MemoryStatus.EXPIRED.value, _dt_dump(now), owner_id, namespace,
                 MemoryStatus.ACTIVE.value, _dt_dump(now)),
            )
            return cursor.rowcount

    def delete(self, memory_id: str, *, owner_id: str, namespace: str) -> int:
        """Physically delete the target memory and its entire version lineage."""
        self.get(memory_id, owner_id=owner_id, namespace=namespace)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT memory_id, supersedes_memory_id FROM memories WHERE owner_id = ? AND namespace = ?",
                (owner_id, namespace),
            ).fetchall()
            parent_by_id = {row["memory_id"]: row["supersedes_memory_id"] for row in rows}
            family = {memory_id}
            changed = True
            while changed:
                changed = False
                for candidate_id, parent_id in parent_by_id.items():
                    if candidate_id in family or parent_id in family:
                        before = len(family)
                        family.add(candidate_id)
                        if parent_id is not None:
                            family.add(parent_id)
                        changed = changed or len(family) != before
            placeholders = ",".join("?" for _ in family)
            cursor = conn.execute(
                f"DELETE FROM memories WHERE owner_id = ? AND namespace = ? AND memory_id IN ({placeholders})",
                [owner_id, namespace, *family],
            )
            return cursor.rowcount
