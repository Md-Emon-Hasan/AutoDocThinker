from typing import Any

from pydantic import BaseModel


class MemoryOut(BaseModel):
    episodic: dict[str, Any]
    facts: list[dict[str, Any]]


class MemoryDeleteOut(BaseModel):
    session_id: str
    turns_removed: int
    facts_removed: int
    embeddings_removed: int
