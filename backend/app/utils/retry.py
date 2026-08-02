def should_retry(attempt: int, max_attempts: int) -> bool:
    return attempt < max_attempts


def backoff_seconds(attempt: int, base: float = 0.5, cap: float = 8.0) -> float:
    """Exponential-with-cap backoff delay for retry attempt ``attempt``.

    Deterministic (no jitter) by default so callers relying on it stay
    reproducible in tests; ``attempt`` is 0-indexed.
    """
    return min(base * (2**attempt), cap)
