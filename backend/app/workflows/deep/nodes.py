"""Placeholder nodes for the future `deep` orchestration workflow (Stage 6).

Not reachable via any route or RAGService mode in Stage 0 — this package
only establishes the on-disk shape matching the other four workflows
(naive/advanced/crag/self_rag) so Stage 6 has a consistent starting point
for the real planner/sub-agent/synthesis logic.
"""


def plan_node(state: dict) -> dict:
    return {
        **state,
        "answer": "deep mode is not yet implemented (scaffolded in Stage 0, "
        "implemented in Stage 6)",
    }
