from typing import Any, TypedDict


class BaseState(TypedDict, total=False):
    input: str
    domain: str
    mode: str
    history: list[dict[str, str]]
    metadata_filter: dict[str, Any] | None
    context_docs: list[Any]
    answer: str
    sources: list[dict[str, Any]]
    confidence: float
    retry_count: int


class NaiveState(BaseState, total=False):
    next_agent: str


class AdvancedState(BaseState, total=False):
    rewritten_queries: list[str]


class CRAGState(BaseState, total=False):
    retrieval_score: float
    next_agent: str


class SelfRAGState(BaseState, total=False):
    need_retrieval: bool
    draft_answer: str
    critique: str
    next_agent: str


RAGState = BaseState
