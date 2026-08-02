from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubTask:
    id: str
    query: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class SubAgentResult:
    subtask_id: str
    answer: str
    sources: list[dict[str, Any]]
    success: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "subtask_id": self.subtask_id,
            "answer": self.answer,
            "sources": self.sources,
            "success": self.success,
            "error": self.error,
        }
