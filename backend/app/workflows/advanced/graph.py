from langgraph.graph import END, START, StateGraph

from app.rag.state import AdvancedState
from app.workflows.advanced.edges import has_rewrites
from app.workflows.advanced.nodes import answer_node, retrieve_node, rewrite_node


def _build_graph(retrieval, llm, domain_profile):
    graph = StateGraph(AdvancedState)
    graph.add_node("rewrite", lambda state: rewrite_node(state, domain_profile))
    graph.add_node("retrieve", lambda state: retrieve_node(state, retrieval))
    graph.add_node("answer", lambda state: answer_node(state, llm, domain_profile))
    graph.add_edge(START, "rewrite")
    graph.add_conditional_edges(
        "rewrite", has_rewrites, {True: "retrieve", False: "answer"}
    )
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def run_advanced(state: dict, retrieval, llm, domain_profile) -> dict:
    return _build_graph(retrieval, llm, domain_profile).invoke(state)
