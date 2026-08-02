from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    domain: str = "general"
    rag_mode: str = "advanced"
    history: list[dict[str, str]] = Field(default_factory=list)
    metadata_filter: dict[str, Any] | None = None
    scope: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]]
    history: list[dict[str, str]]
    mode: str
    domain: str
    metadata: dict[str, Any]
    verification: dict[str, Any] | None = None
    governance: dict[str, Any] | None = None
    hitl: dict[str, Any] | None = None
