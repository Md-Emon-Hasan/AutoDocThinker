from app.orchestration.models import SubAgentResult
from app.rag.formatting import format_context_with_sources


class SubAgent:
    """Each sub-agent receives a scoped, minimal context: its own
    sub-task and the retrieval results it needs -- no other sub-tasks'
    results, no shared state. Inherits the caller's scope via
    ``metadata_filter``."""

    def __init__(self, retrieval, llm, domain_profile, metadata_filter) -> None:
        self.retrieval = retrieval
        self.llm = llm
        self.domain_profile = domain_profile
        self.metadata_filter = metadata_filter

    def run(self, subtask) -> SubAgentResult:
        """A sub-agent failure must not fail the query -- caught here,
        never propagated, so the caller can synthesize from the rest."""
        try:
            docs = self.retrieval.retrieve(subtask.query, 6, self.metadata_filter)
            context, sources = format_context_with_sources(docs)
            answer = self.llm.answer(
                subtask.query, context, self.domain_profile.system_prompt
            )
            return SubAgentResult(
                subtask_id=subtask.id, answer=answer, sources=sources, success=True
            )
        except Exception as exc:
            return SubAgentResult(
                subtask_id=subtask.id,
                answer="",
                sources=[],
                success=False,
                error=str(exc),
            )
