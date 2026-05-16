def should_fallback(state: dict) -> bool:
    return not bool(state.get("context_docs"))
