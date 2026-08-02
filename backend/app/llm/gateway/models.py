from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TaskCategory(str, Enum):
    """Declared purpose of an LLM call, used to route to a task-specific
    model. QUERY_REWRITE/COMPRESSION/RELEVANCE_SCORING/TITLE_GENERATION/
    SELF_RAG_CRITIQUE have no real call site yet -- reserved so adding one
    later doesn't need another breaking change to this enum."""

    ANSWER_GENERATION = "answer_generation"
    QUERY_REWRITE = "query_rewrite"
    COMPRESSION = "compression"
    RELEVANCE_SCORING = "relevance_scoring"
    TITLE_GENERATION = "title_generation"
    VERIFICATION = "verification"
    SELF_RAG_CRITIQUE = "self_rag_critique"
    MEMORY_EXTRACTION = "memory_extraction"
    DEEP_PLANNING = "deep_planning"


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

    def answer(self, question: str, context: str, domain_prompt: str) -> str:
        raise NotImplementedError
