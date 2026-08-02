import contextlib
import sqlite3
import time
from pathlib import Path

from app.utils.hashing import sha1_short

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    scope TEXT,
    rule TEXT NOT NULL,
    action TEXT NOT NULL,
    reason_hash TEXT
)
"""


class AuditLog:
    """Every governance/HITL decision, persisted to SQLite.

    Never stores raw PII or blocked content: only a hash of the reason
    plus the rule identifier that fired, per the spec's "debuggable
    without storing raw PII" requirement.
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

    def record(
        self, scope: str | None, rule: str, action: str, reason: str = ""
    ) -> None:
        reason_hash = sha1_short(reason) if reason else None
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO audit_log (timestamp, scope, rule, action, reason_hash) "
                "VALUES (?, ?, ?, ?, ?)",
                (time.time(), scope, rule, action, reason_hash),
            )

    def list(self, limit: int = 50, offset: int = 0) -> dict:
        with contextlib.closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) AS c FROM audit_log").fetchone()["c"]
        return {"items": [dict(row) for row in rows], "total": total}
