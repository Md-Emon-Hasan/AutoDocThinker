def needs_web_search(state: dict, threshold: float = 0.6) -> bool:
    return float(state.get("confidence", 0.0)) < threshold
