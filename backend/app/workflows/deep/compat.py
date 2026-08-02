from app.workflows.deep.graph import run_deep


def build_deep_rag(*args, **kwargs):
    return lambda state: run_deep(state)
