import contextlib
import json
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from app.memory.models import EpisodicTurn, SemanticFact

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodic_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    sources TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_turns(session_id);

CREATE TABLE IF NOT EXISTS semantic_facts (
    id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    text TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    source_turn TEXT,
    supersedes TEXT,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_semantic_scope ON semantic_facts(scope);
"""


class MemoryStore:
    """One SQLite database, two tables (episodic turns, semantic facts) --
    one store, two record types, not two memory systems."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._version = 0
        with contextlib.closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---- episodic -------------------------------------------------------

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: list[str] | None = None,
        now: float | None = None,
    ) -> EpisodicTurn:
        turn = EpisodicTurn(
            session_id=session_id,
            role=role,
            content=content,
            timestamp=now if now is not None else time.time(),
            sources=sources or [],
        )
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO episodic_turns (session_id, role, content, timestamp, "
                "sources) VALUES (?, ?, ?, ?, ?)",
                (
                    turn.session_id,
                    turn.role,
                    turn.content,
                    turn.timestamp,
                    json.dumps(turn.sources),
                ),
            )
        return turn

    def get_turns(self, session_id: str, limit: int = 100, offset: int = 0) -> dict:
        with contextlib.closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM episodic_turns WHERE session_id = ? "
                "ORDER BY id ASC LIMIT ? OFFSET ?",
                (session_id, limit, offset),
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM episodic_turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()["c"]
        items = [
            EpisodicTurn(
                session_id=r["session_id"],
                role=r["role"],
                content=r["content"],
                timestamp=r["timestamp"],
                sources=json.loads(r["sources"]),
            ).to_dict()
            for r in rows
        ]
        return {"items": items, "total": total}

    # ---- semantic --------------------------------------------------------

    def add_fact(
        self,
        scope: str,
        text: str,
        confidence: float,
        source_turn: str | None = None,
        supersedes: str | None = None,
        now: float | None = None,
    ) -> SemanticFact:
        ts = now if now is not None else time.time()
        fact = SemanticFact(
            id=str(uuid4()),
            scope=scope,
            text=text,
            confidence=confidence,
            created_at=ts,
            updated_at=ts,
            source_turn=source_turn,
            supersedes=supersedes,
        )
        with contextlib.closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO semantic_facts (id, scope, text, confidence, "
                "created_at, updated_at, source_turn, supersedes, active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (
                    fact.id,
                    fact.scope,
                    fact.text,
                    fact.confidence,
                    fact.created_at,
                    fact.updated_at,
                    fact.source_turn,
                    fact.supersedes,
                ),
            )
            if supersedes:
                conn.execute(
                    "UPDATE semantic_facts SET active = 0 WHERE id = ?", (supersedes,)
                )
        self._version += 1
        return fact

    def _row_to_fact(self, row: sqlite3.Row) -> SemanticFact:
        return SemanticFact(
            id=row["id"],
            scope=row["scope"],
            text=row["text"],
            confidence=row["confidence"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            source_turn=row["source_turn"],
            supersedes=row["supersedes"],
            active=bool(row["active"]),
        )

    def list_facts(
        self, scope: str, include_superseded: bool = False
    ) -> list[SemanticFact]:
        query = "SELECT * FROM semantic_facts WHERE scope = ?"
        if not include_superseded:
            query += " AND active = 1"
        with contextlib.closing(self._connect()) as conn:
            rows = conn.execute(query, (scope,)).fetchall()
        return [self._row_to_fact(r) for r in rows]

    def get_fact(self, fact_id: str) -> SemanticFact | None:
        with contextlib.closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM semantic_facts WHERE id = ?", (fact_id,)
            ).fetchone()
        return self._row_to_fact(row) if row else None

    def decay_facts(
        self,
        scope: str,
        half_life_seconds: float,
        min_confidence: float,
        now: float | None = None,
    ) -> int:
        """Halve confidence per half_life_seconds elapsed; deactivate
        (never delete) facts that decay below min_confidence."""
        now = now if now is not None else time.time()
        deactivated = 0
        with contextlib.closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT * FROM semantic_facts WHERE scope = ? AND active = 1", (scope,)
            ).fetchall()
            for row in rows:
                age = max(now - row["updated_at"], 0.0)
                decayed = row["confidence"] * (0.5 ** (age / half_life_seconds))
                if decayed < min_confidence:
                    conn.execute(
                        "UPDATE semantic_facts SET active = 0, confidence = ? WHERE id = ?",
                        (decayed, row["id"]),
                    )
                    deactivated += 1
                else:
                    conn.execute(
                        "UPDATE semantic_facts SET confidence = ? WHERE id = ?",
                        (decayed, row["id"]),
                    )
        if deactivated:
            self._version += 1
        return deactivated

    # ---- lifecycle ---------------------------------------------------

    def delete_session(self, session_id: str) -> dict:
        """Remove episodic turns (keyed by session_id) and semantic facts
        (keyed by "session:<id>" scope) for this session. Caller is
        responsible for also clearing the fact Chroma collection."""
        scope = f"session:{session_id}"
        with contextlib.closing(self._connect()) as conn, conn:
            turns_cursor = conn.execute(
                "DELETE FROM episodic_turns WHERE session_id = ?", (session_id,)
            )
            facts_cursor = conn.execute(
                "DELETE FROM semantic_facts WHERE scope = ?", (scope,)
            )
        self._version += 1
        return {
            "turns_removed": turns_cursor.rowcount,
            "facts_removed": facts_cursor.rowcount,
        }

    @property
    def version(self) -> int:
        """Monotonic counter bumped on any fact add/decay/delete -- used
        as the memory-state component of Stage 2's answer cache key."""
        return self._version
