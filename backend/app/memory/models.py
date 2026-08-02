from dataclasses import dataclass, field
from typing import Any


@dataclass
class EpisodicTurn:
    session_id: str
    role: str
    content: str
    timestamp: float
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "sources": list(self.sources),
        }


@dataclass
class SemanticFact:
    id: str
    scope: str
    text: str
    confidence: float
    created_at: float
    updated_at: float
    source_turn: str | None = None
    supersedes: str | None = None
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scope": self.scope,
            "text": self.text,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source_turn": self.source_turn,
            "supersedes": self.supersedes,
            "active": self.active,
        }
