from app.rag.formatting import format_context_with_sources
from app.rag.modes import ensure_mode
from app.workflows.advanced import run_advanced
from app.workflows.crag import run_crag
from app.workflows.finalize import finalize
from app.workflows.naive import run_naive
from app.workflows.self_rag import run_self_rag


class RAGService:
    def __init__(self, domains, retrieval, llm, wiki) -> None:
        self.domains = domains
        self.retrieval = retrieval
        self.llm = llm
        self.wiki = wiki

    def query(
        self, question: str, domain: str, mode: str, history=None, metadata_filter=None
    ) -> dict:
        clean_mode = ensure_mode(mode)
        profile = self.domains.get(domain)
        merged_filter = {**profile.metadata_filter, **(metadata_filter or {})}
        state = {
            "input": question,
            "domain": profile.name,
            "mode": clean_mode,
            "history": history or [],
            "metadata_filter": merged_filter or None,
            "formatter": format_context_with_sources,
        }
        if clean_mode == "naive":
            result = run_naive(state, self.retrieval, self.llm, profile)
        elif clean_mode == "advanced":
            result = run_advanced(state, self.retrieval, self.llm, profile)
        elif clean_mode == "crag":
            result = run_crag(state, self.retrieval, self.llm, profile, self.wiki)
        else:
            result = run_self_rag(state, self.retrieval, self.llm, profile)
        result = finalize(result)
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "history": result["history"],
            "mode": clean_mode,
            "domain": profile.name,
            "metadata": {
                key: result[key]
                for key in ("confidence", "need_retrieval", "rewritten_queries")
                if key in result
            },
        }


def process_query(
    rag_service: RAGService,
    input_text: str,
    file_path=None,
    file_type=None,
    mode: str = "advanced",
    history=None,
    metadata_filter=None,
    domain: str = "general",
) -> dict:
    if file_path or file_type:
        metadata_filter = metadata_filter or {}
    return rag_service.query(input_text, domain, mode, history or [], metadata_filter)
