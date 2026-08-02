"""No conditional edges: deep/graph.py is a single-node StateGraph
(orchestrate -> END). Planner dependency-graph routing and sub-agent
dispatch decisions happen inside DeepOrchestrator.run() (see
app/orchestration/orchestrator.py), not as LangGraph conditional edges --
that fan-out/dependency-graph shape doesn't map onto StateGraph's
linear-pipeline edge model the way the other four workflows' branching
does.
"""
