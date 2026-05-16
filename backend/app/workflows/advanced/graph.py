from app.workflows.advanced.nodes import answer_node, retrieve_node, rewrite_node


def run_advanced(state: dict, retrieval, llm, domain_profile) -> dict:
    return answer_node(
        retrieve_node(rewrite_node(state, domain_profile), retrieval),
        llm,
        domain_profile,
    )
