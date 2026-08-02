"""A newer contradicting fact supersedes the old one -- marked
superseded, never deleted, never retrieved again."""

import json

from app.memory.extraction import detect_contradiction, run_extraction_job
from app.memory.store import MemoryStore


class _StubTaskClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def answer(self, question, context, domain_prompt):
        response = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return response


class TestSupersession:
    def test_add_fact_with_supersedes_marks_old_inactive(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        old = store.add_fact("session:s1", "prefers tea", confidence=0.8)
        store.add_fact(
            "session:s1", "prefers coffee", confidence=0.9, supersedes=old.id
        )

        active = store.list_facts("session:s1")
        assert len(active) == 1
        assert active[0].text == "prefers coffee"

    def test_superseded_fact_never_retrieved_by_default(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        old = store.add_fact("session:s1", "prefers tea", confidence=0.8)
        store.add_fact(
            "session:s1", "prefers coffee", confidence=0.9, supersedes=old.id
        )

        assert old.id not in {f.id for f in store.list_facts("session:s1")}

    def test_superseded_fact_not_deleted_only_deactivated(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        old = store.add_fact("session:s1", "prefers tea", confidence=0.8)
        store.add_fact(
            "session:s1", "prefers coffee", confidence=0.9, supersedes=old.id
        )

        with_superseded = store.list_facts("session:s1", include_superseded=True)
        assert any(f.id == old.id and not f.active for f in with_superseded)


class TestContradictionDetection:
    def test_detects_contradicting_fact_index(self):
        client = _StubTaskClient([json.dumps({"contradicts_index": 0})])

        class _Fact:
            def __init__(self, text):
                self.text = text

        existing = [_Fact("prefers tea")]
        result = detect_contradiction("prefers coffee", existing, client)
        assert result == 0

    def test_no_contradiction_returns_none(self):
        client = _StubTaskClient([json.dumps({"contradicts_index": None})])

        class _Fact:
            def __init__(self, text):
                self.text = text

        result = detect_contradiction("likes hiking", [_Fact("prefers tea")], client)
        assert result is None

    def test_no_existing_facts_returns_none_without_calling_client(self):
        calls = []

        class _CountingClient:
            def answer(self, *a, **k):
                calls.append(1)
                return "{}"

        result = detect_contradiction("new fact", [], _CountingClient())
        assert result is None
        assert calls == []


class TestExtractionJobSupersession:
    def test_contradiction_during_extraction_supersedes(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        old = store.add_fact("session:s1", "prefers tea", confidence=0.8)

        client = _StubTaskClient(
            [
                json.dumps({"facts": [{"text": "prefers coffee", "confidence": 0.9}]}),
                json.dumps({"contradicts_index": 0}),
            ]
        )
        run_extraction_job(store, None, client, "session:s1", "q", "a")

        active = store.list_facts("session:s1")
        assert len(active) == 1
        assert active[0].text == "prefers coffee"
        assert active[0].supersedes == old.id
