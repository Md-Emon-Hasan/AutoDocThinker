from langgraph.graph import END, START, StateGraph

from app.rag.state import BaseState
from app.workflows.deep.nodes import plan_node


def _build_graph():
    graph = StateGraph(BaseState)
    graph.add_node("plan", plan_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", END)
    return graph.compile()


def run_deep(state: dict, *args, **kwargs) -> dict:
    """Scaffold only — not wired into RAGService.query or RAG_MODES.

    Stage 6 replaces this with the real planner -> scoped sub-agents ->
    synthesis graph. Kept deliberately minimal so it can't be reached or
    accidentally exercised before then.
    """
    return _build_graph().invoke(state)
