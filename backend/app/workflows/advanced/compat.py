from typing import Optional, Tuple

from app.ingestion.document import Document
from app.retrieval.compressor import compress_documents
from app.workflows.advanced.graph import run_advanced
from app.workflows.advanced.nodes import answer_node, retrieve_node, rewrite_node


def _compress_one(args: Tuple[str, Document, float]) -> Optional[Document]:
    q, doc, score = args
    if not doc:
        return None
    if len(doc.page_content) > 3000:
        doc.page_content = doc.page_content[:3000].rstrip()
    return doc


def advanced_ingest(state: dict) -> dict:
    return state


def advanced_rewrite(state: dict, domain_profile) -> dict:
    return rewrite_node(state, domain_profile)


def advanced_retrieve(state: dict, retrieval) -> dict:
    return retrieve_node(state, retrieval)


def advanced_compress(state: dict) -> dict:
    return {**state, "context_docs": compress_documents(state.get("context_docs", []))}


def advanced_answer(state: dict, llm, domain_profile) -> dict:
    return answer_node(state, llm, domain_profile)


def advanced_fallback(state: dict, llm, domain_profile) -> dict:
    return answer_node({**state, "context_docs": []}, llm, domain_profile)


def build_advanced_rag(retrieval, llm, domain_profile):
    return lambda state: run_advanced(state, retrieval, llm, domain_profile)
