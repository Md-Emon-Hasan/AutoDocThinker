def should_retrieve(state: dict) -> bool:
    return bool(state.get("need_retrieval"))
