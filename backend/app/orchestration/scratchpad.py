import contextlib
import json
import sqlite3
import time
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scratchpad (
    query_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    subtasks TEXT NOT NULL,
    statuses TEXT NOT NULL,
    notes TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
)
"""


class ScratchpadStore:
    """A durable per-query task list with per-sub-task status and
    intermediate notes -- the "deep agent" planning layer, persisted to
    the same SQLite file as Stage 5's MemoryStore (a separate table, own
    connections) so a long query can be inspected, and in principle
    resumed, across a restart.
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

    def save(self, query_id: str, question: str, subtasks: list) -> None:
        now = time.time()
        statuses = {t.id: "pending" for t in subtasks}
        subtasks_json = json.dumps(
            [
                {"id": t.id, "query": t.query, "depends_on": t.depends_on}
                for t in subtasks
            ]
        )
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO scratchpad (query_id, question, subtasks, statuses, "
                "notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(query_id) DO UPDATE SET subtasks=excluded.subtasks, "
                "statuses=excluded.statuses, updated_at=excluded.updated_at",
                (
                    query_id,
                    question,
                    subtasks_json,
                    json.dumps(statuses),
                    json.dumps({}),
                    now,
                    now,
                ),
            )

    def update_status(
        self, query_id: str, subtask_id: str, status: str, note: str | None = None
    ) -> None:
        record = self.get(query_id)
        if record is None:
            return
        statuses = record["statuses"]
        statuses[subtask_id] = status
        notes = record["notes"]
        if note is not None:
            notes[subtask_id] = note
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE scratchpad SET statuses = ?, notes = ?, updated_at = ? "
                "WHERE query_id = ?",
                (json.dumps(statuses), json.dumps(notes), time.time(), query_id),
            )

    def get(self, query_id: str) -> dict | None:
        with contextlib.closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM scratchpad WHERE query_id = ?", (query_id,)
            ).fetchone()
        if row is None:
            return None
        return {
            "query_id": row["query_id"],
            "question": row["question"],
            "subtasks": json.loads(row["subtasks"]),
            "statuses": json.loads(row["statuses"]),
            "notes": json.loads(row["notes"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
