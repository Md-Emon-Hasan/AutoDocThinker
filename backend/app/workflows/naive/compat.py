from app.workflows.naive.edges import should_fallback
from app.workflows.naive.graph import run_naive
from app.workflows.naive.nodes import answer_node, retrieve_node


def naive_router(state: dict) -> dict:
    return {**state, "next_agent": "fallback" if should_fallback(state) else "answer"}


def naive_ingest(state: dict) -> dict:
    return state


def naive_retrieve(state: dict, retrieval) -> dict:
    return retrieve_node(state, retrieval)


def naive_answer(state: dict, llm, domain_profile) -> dict:
    return answer_node(state, llm, domain_profile)


def naive_fallback(state: dict, llm, domain_profile) -> dict:
    return answer_node({**state, "context_docs": []}, llm, domain_profile)


def build_naive_rag(retrieval, llm, domain_profile):
    return lambda state: run_naive(state, retrieval, llm, domain_profile)
