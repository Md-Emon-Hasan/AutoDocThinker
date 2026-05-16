def should_retry(attempt: int, max_attempts: int) -> bool:
    return attempt < max_attempts
