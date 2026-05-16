from app.workflows.self_rag.graph import run_self_rag
from app.workflows.self_rag.nodes import decide_node, generate_node


def self_rag_ingest(state: dict) -> dict:
    return state


def self_rag_decide(state: dict, retrieval) -> dict:
    return decide_node(state, retrieval)


def self_rag_retrieve(state: dict, retrieval) -> dict:
    return decide_node(state, retrieval)


def self_rag_generate(state: dict, llm, domain_profile) -> dict:
    return generate_node(state, llm, domain_profile)


def self_rag_critique(state: dict) -> dict:
    return {**state, "critique": "No issues detected.", "next_agent": "finalize"}


def self_rag_revise(state: dict) -> dict:
    return {**state, "answer": state.get("draft_answer", state.get("answer", ""))}


def build_self_rag(retrieval, llm, domain_profile):
    return lambda state: run_self_rag(state, retrieval, llm, domain_profile)
