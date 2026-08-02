"""Scaffold package for the future `deep` orchestration workflow.

Deliberately NOT imported by app.rag.service, app.rag.modes, or any API
route in Stage 0 — registering it as a reachable fifth mode is Stage 6
scope. This package exists only so Stage 6 has the same on-disk shape
(graph.py/nodes.py/edges.py/compat.py) as the other four workflows.
"""

from app.workflows.deep.compat import build_deep_rag
from app.workflows.deep.graph import run_deep

__all__ = ["run_deep", "build_deep_rag"]
