from app.workflows.crag.edges import needs_web_search
from app.workflows.crag.nodes import (
    answer_node,
    evaluate_node,
    retrieve_node,
    web_search_node,
)


def run_crag(state: dict, retrieval, llm, domain_profile, wiki) -> dict:
    state = evaluate_node(retrieve_node(state, retrieval))
    if needs_web_search(state):
        state = web_search_node(state, wiki)
    return answer_node(state, llm, domain_profile)
