def has_rewrites(state: dict) -> bool:
    return bool(state.get("rewritten_queries"))
