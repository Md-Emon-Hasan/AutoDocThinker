def remember(
    history: list[dict[str, str]], role: str, content: str
) -> list[dict[str, str]]:
    return [*history, {"role": role, "content": content}]
