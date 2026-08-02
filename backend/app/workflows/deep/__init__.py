"""Stage 6: the `deep` orchestration workflow -- a fifth RAG mode.

Planner -> scoped sub-agents (parallel, budget-capped) -> synthesis. See
app/orchestration/ for the real implementation; this package just gives
it the same on-disk shape (graph.py/nodes.py/edges.py/compat.py) as the
other four workflows.
"""

from app.workflows.deep.compat import build_deep_rag
from app.workflows.deep.graph import run_deep

__all__ = ["run_deep", "build_deep_rag"]
