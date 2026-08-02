from langgraph.graph import END, START, StateGraph

from app.rag.state import CRAGState
from app.workflows.crag.edges import needs_web_search
from app.workflows.crag.nodes import (
    answer_node,
    evaluate_node,
    retrieve_node,
    web_search_node,
)


def _build_graph(retrieval, llm, domain_profile, wiki):
    graph = StateGraph(CRAGState)
    graph.add_node("retrieve", lambda state: retrieve_node(state, retrieval))
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("web_search", lambda state: web_search_node(state, wiki))
    graph.add_node("answer", lambda state: answer_node(state, llm, domain_profile))
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        lambda state: needs_web_search(state),
        {True: "web_search", False: "answer"},
    )
    graph.add_edge("web_search", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def run_crag(state: dict, retrieval, llm, domain_profile, wiki) -> dict:
    return _build_graph(retrieval, llm, domain_profile, wiki).invoke(state)
