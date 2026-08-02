from app.workflows.deep.graph import run_deep


def build_deep_rag(retrieval, llm, domain_profile, orchestrator):
    return lambda state: run_deep(state, retrieval, llm, domain_profile, orchestrator)
