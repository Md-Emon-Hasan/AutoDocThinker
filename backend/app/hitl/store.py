import contextlib
import json
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from app.hitl.models import PendingItem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS hitl_pending (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    reason TEXT NOT NULL,
    proposed_output TEXT NOT NULL,
    scope TEXT,
    created_at REAL NOT NULL,
    status TEXT NOT NULL,
    decision_reason TEXT,
    final_output TEXT,
    expires_at REAL
)
"""


class HITLStore:
    """SQLite-backed pending-approval queue.

    app/chat/history_store.py is in-memory and cannot back this: pending
    approvals must survive a process restart, which is the entire point
    of gating a request rather than blocking on it in memory.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_item(self, row: sqlite3.Row) -> PendingItem:
        return PendingItem(
            id=row["id"],
            kind=row["kind"],
            reason=row["reason"],
            proposed_output=json.loads(row["proposed_output"]),
            scope=row["scope"],
            created_at=row["created_at"],
            status=row["status"],
            decision_reason=row["decision_reason"],
            final_output=(
                json.loads(row["final_output"]) if row["final_output"] else None
            ),
            expires_at=row["expires_at"],
        )

    def create(
        self,
        kind: str,
        reason: str,
        proposed_output: dict,
        scope: str | None,
        ttl_seconds: float | None,
        now: float | None = None,
    ) -> PendingItem:
        item = PendingItem(
            id=str(uuid4()),
            kind=kind,
            reason=reason,
            proposed_output=proposed_output,
            scope=scope,
            created_at=now if now is not None else time.time(),
            expires_at=(
                (now if now is not None else time.time()) + ttl_seconds
                if ttl_seconds
                else None
            ),
        )
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO hitl_pending (id, kind, reason, proposed_output, scope, "
                "created_at, status, decision_reason, final_output, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.id,
                    item.kind,
                    item.reason,
                    json.dumps(item.proposed_output),
                    item.scope,
                    item.created_at,
                    item.status,
                    item.decision_reason,
                    None,
                    item.expires_at,
                ),
            )
        return item

    def get(self, item_id: str) -> PendingItem | None:
        with contextlib.closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM hitl_pending WHERE id = ?", (item_id,)
            ).fetchone()
        return self._row_to_item(row) if row else None

    def list_pending(self, limit: int = 50, offset: int = 0) -> dict:
        with contextlib.closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM hitl_pending WHERE status = 'pending' "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM hitl_pending WHERE status = 'pending'"
            ).fetchone()["c"]
        return {"items": [self._row_to_item(r).to_dict() for r in rows], "total": total}

    def _set_status(
        self,
        item_id: str,
        status: str,
        decision_reason: str | None,
        final_output: dict | None,
    ) -> PendingItem | None:
        item = self.get(item_id)
        if item is None:
            return None
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE hitl_pending SET status = ?, decision_reason = ?, "
                "final_output = ? WHERE id = ?",
                (
                    status,
                    decision_reason,
                    json.dumps(final_output) if final_output is not None else None,
                    item_id,
                ),
            )
        return self.get(item_id)

    def approve(self, item_id: str, reason: str | None = None) -> PendingItem | None:
        item = self.get(item_id)
        final_output = item.proposed_output if item else None
        return self._set_status(item_id, "approved", reason, final_output)

    def reject(self, item_id: str, reason: str | None = None) -> PendingItem | None:
        return self._set_status(item_id, "rejected", reason, None)

    def edit_and_approve(
        self, item_id: str, edited_output: dict, reason: str | None = None
    ) -> PendingItem | None:
        return self._set_status(item_id, "approved", reason, edited_output)

    def expire_stale(
        self, default_action: str = "reject", now: float | None = None
    ) -> int:
        """Expire pending items past their TTL. Returns count expired."""
        now = now if now is not None else time.time()
        with contextlib.closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT id FROM hitl_pending WHERE status = 'pending' "
                "AND expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            ).fetchall()
            status = "approved" if default_action == "approve" else "rejected"
            for row in rows:
                conn.execute(
                    "UPDATE hitl_pending SET status = ?, decision_reason = ? WHERE id = ?",
                    (status, f"expired -> default action: {default_action}", row["id"]),
                )
        return len(rows)
