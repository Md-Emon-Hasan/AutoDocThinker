from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TaskCategory(str, Enum):
    """Declared purpose of an LLM call, used to route to a sized model.

    Only ANSWER_GENERATION has a real call site today (RAGService's
    answer-generation path via GroqClient). The rest are reserved for
    later stages (Stage 3's verifier/critic, a future real query-rewrite
    or wikipedia-summarization LLM call) so the category taxonomy doesn't
    need another breaking change when those call sites appear.
    """

    ANSWER_GENERATION = "answer_generation"
    QUERY_REWRITE = "query_rewrite"
    COMPRESSION = "compression"
    RELEVANCE_SCORING = "relevance_scoring"
    TITLE_GENERATION = "title_generation"
    VERIFICATION = "verification"
    SELF_RAG_CRITIQUE = "self_rag_critique"


@dataclass(frozen=True)
class GatewayRequest:
    question: str
    context: str
    domain_prompt: str
    task: TaskCategory
    complexity_hint: float | None = None


@dataclass(frozen=True)
class GatewayResponse:
    text: str
    provider: str
    attempts: int


class Provider(Protocol):
    """Structural protocol every gateway provider must satisfy.

    Matches GroqClient's existing method exactly, so GroqClient becomes a
    provider with zero code changes (duck typing, no inheritance needed).
    """

    def answer(self, question: str, context: str, domain_prompt: str) -> str: ...
