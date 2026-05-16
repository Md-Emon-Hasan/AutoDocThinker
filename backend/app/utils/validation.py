def require_non_empty(value: str, name: str) -> str:
    if not value.strip():
        raise ValueError(f"{name} is required")
    return value
