from app.workflows.crag.graph import run_crag
from app.workflows.crag.nodes import (
    answer_node,
    evaluate_node,
    retrieve_node,
    web_search_node,
)


def crag_ingest(state: dict) -> dict:
    return state


def crag_retrieve(state: dict, retrieval) -> dict:
    return retrieve_node(state, retrieval)


def crag_evaluate(state: dict) -> dict:
    return evaluate_node(state)


def crag_web_search(state: dict, wiki) -> dict:
    return web_search_node(state, wiki)


def crag_answer(state: dict, llm, domain_profile) -> dict:
    return answer_node(state, llm, domain_profile)


def build_crag(retrieval, llm, domain_profile, wiki):
    return lambda state: run_crag(state, retrieval, llm, domain_profile, wiki)
