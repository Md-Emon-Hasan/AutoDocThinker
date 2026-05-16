from app.workflows.naive.nodes import answer_node, retrieve_node


def run_naive(state: dict, retrieval, llm, domain_profile) -> dict:
    return answer_node(retrieve_node(state, retrieval), llm, domain_profile)
