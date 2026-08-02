class HistoryStore:
    """Stage 5: optionally backed by app/memory/store.py::MemoryStore for
    durability, without changing this class's public interface --
    set()'s signature and _items' in-memory-cache role are unchanged, so
    existing callers/tests are unaffected whether or not a memory_store
    is supplied.
    """

    def __init__(self, memory_store=None) -> None:
        self._items: dict[str, list[dict[str, str]]] = {}
        self._memory_store = memory_store
        self._persisted_counts: dict[str, int] = {}

    def set(self, session_id: str, history: list[dict[str, str]]) -> None:
        self._items[session_id] = history
        if self._memory_store is not None:
            already = self._persisted_counts.get(session_id, 0)
            for turn in history[already:]:
                self._memory_store.add_turn(
                    session_id, turn.get("role", ""), turn.get("content", "")
                )
            self._persisted_counts[session_id] = len(history)

    def get(self, session_id: str) -> list[dict[str, str]]:
        """Additive: durable lookup, falling back to the memory store so
        a session's history survives a restart even if this in-process
        cache was just created fresh."""
        if session_id in self._items:
            return self._items[session_id]
        if self._memory_store is not None:
            turns = self._memory_store.get_turns(session_id)["items"]
            history = [{"role": t["role"], "content": t["content"]} for t in turns]
            if history:
                self._items[session_id] = history
                self._persisted_counts[session_id] = len(history)
            return history
        return []
