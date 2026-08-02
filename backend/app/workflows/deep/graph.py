from langgraph.graph import END, START, StateGraph

from app.rag.state import DeepState
from app.workflows.deep.nodes import orchestrate_node


def _build_graph(orchestrator, domain_profile):
    graph = StateGraph(DeepState)
    graph.add_node(
        "orchestrate",
        lambda state: orchestrate_node(state, orchestrator, domain_profile),
    )
    graph.add_edge(START, "orchestrate")
    graph.add_edge("orchestrate", END)
    return graph.compile()


def run_deep(state: dict, retrieval, llm, domain_profile, orchestrator) -> dict:
    """Planner -> scoped sub-agents -> synthesis (app/orchestration/).
    A single-node StateGraph -- the real parallel fan-out happens inside
    DeepOrchestrator.run(), not as separate graph nodes.
    """
    return _build_graph(orchestrator, domain_profile).invoke(state)
