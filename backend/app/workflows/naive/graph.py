from langgraph.graph import END, START, StateGraph

from app.rag.state import NaiveState
from app.workflows.naive.edges import should_fallback
from app.workflows.naive.nodes import answer_node, retrieve_node


def _router_node(state: dict) -> dict:
    return {**state, "next_agent": "fallback" if should_fallback(state) else "answer"}


def _route_decision(state: dict) -> str:
    return state["next_agent"]


def _build_graph(retrieval, llm, domain_profile):
    graph = StateGraph(NaiveState)
    graph.add_node("retrieve", lambda state: retrieve_node(state, retrieval))
    graph.add_node("router", _router_node)
    graph.add_node("answer", lambda state: answer_node(state, llm, domain_profile))
    graph.add_node(
        "fallback",
        lambda state: answer_node({**state, "context_docs": []}, llm, domain_profile),
    )
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "router")
    graph.add_conditional_edges(
        "router", _route_decision, {"answer": "answer", "fallback": "fallback"}
    )
    graph.add_edge("answer", END)
    graph.add_edge("fallback", END)
    return graph.compile()


def run_naive(state: dict, retrieval, llm, domain_profile) -> dict:
    return _build_graph(retrieval, llm, domain_profile).invoke(state)
