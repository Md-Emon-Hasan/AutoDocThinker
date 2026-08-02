from langgraph.graph import END, START, StateGraph

from app.rag.state import SelfRAGState
from app.workflows.self_rag.nodes import decide_node, generate_node

# NOTE (Stage 3 TODO): self_rag_critique/self_rag_revise (compat.py) are not
# wired into this graph. Wiring them in belongs to Stage 3's Critic
# consolidation — it would change today's answer (always the raw
# generate_node output) by rewriting it, which is out of scope for a
# behavior-preserving substrate conversion. When Stage 3 lands, add a
# conditional edge: decide -> generate -> critique -> [revise|END].


def _build_graph(retrieval, llm, domain_profile):
    graph = StateGraph(SelfRAGState)
    graph.add_node("decide", lambda state: decide_node(state, retrieval))
    graph.add_node("generate", lambda state: generate_node(state, llm, domain_profile))
    graph.add_edge(START, "decide")
    graph.add_edge("decide", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def run_self_rag(state: dict, retrieval, llm, domain_profile) -> dict:
    return _build_graph(retrieval, llm, domain_profile).invoke(state)
