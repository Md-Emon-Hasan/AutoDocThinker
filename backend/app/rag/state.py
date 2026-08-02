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
    # Callable[[list[Any]], tuple[str, list[dict[str, Any]]]] supplied by
    # RAGService.query(); declared here (rather than left undeclared) so
    # LangGraph's StateGraph schema doesn't silently drop it when merging a
    # node's returned state update back into the graph's tracked channels.
    formatter: Any


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


class DeepState(BaseState, total=False):
    orchestration: dict[str, Any]


RAGState = BaseState
