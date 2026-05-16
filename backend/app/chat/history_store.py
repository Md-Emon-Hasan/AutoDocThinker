class HistoryStore:
    def __init__(self) -> None:
        self._items: dict[str, list[dict[str, str]]] = {}

    def set(self, session_id: str, history: list[dict[str, str]]) -> None:
        self._items[session_id] = history
