from app.workflows.self_rag.nodes import decide_node, generate_node


def run_self_rag(state: dict, retrieval, llm, domain_profile) -> dict:
    return generate_node(decide_node(state, retrieval), llm, domain_profile)
