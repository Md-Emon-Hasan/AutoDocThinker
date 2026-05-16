def append_turn(
    history: list[dict[str, str]], question: str, answer: str
) -> list[dict[str, str]]:
    return [
        *history,
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]


def trim_history(
    history: list[dict[str, str]], limit: int = 12
) -> list[dict[str, str]]:
    return history[-limit:]


def history_messages(history: list[dict[str, str]]) -> list[tuple[str, str]]:
    return [(item["role"], item["content"]) for item in history]


def _history_messages(history: list[dict[str, str]]) -> list[tuple[str, str]]:
    return history_messages(history)
