"""Tests for app/memory/extraction.py: background, never blocks the
response, failure doesn't fail the conversation, dedupes."""

import json

from app.memory.extraction import extract_facts, run_extraction_job
from app.memory.store import MemoryStore


class _StubTaskClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def answer(self, question, context, domain_prompt):
        return self._response


class _RaisingTaskClient:
    def answer(self, *args, **kwargs):
        raise RuntimeError("provider outage")


class TestExtractFacts:
    def test_extracts_structured_facts(self):
        client = _StubTaskClient(
            json.dumps({"facts": [{"text": "likes dark mode", "confidence": 0.9}]})
        )
        facts = extract_facts("q", "a", client)
        assert facts == [{"text": "likes dark mode", "confidence": 0.9}]

    def test_no_task_client_returns_empty(self):
        assert extract_facts("q", "a", None) == []

    def test_malformed_json_returns_empty_not_raises(self):
        client = _StubTaskClient("not json at all")
        assert extract_facts("q", "a", client) == []

    def test_client_failure_never_raises(self):
        assert extract_facts("q", "a", _RaisingTaskClient()) == []

    def test_empty_facts_list_returns_empty(self):
        client = _StubTaskClient(json.dumps({"facts": []}))
        assert extract_facts("q", "a", client) == []


class TestRunExtractionJob:
    def test_never_blocks_never_raises_on_failure(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        # Must not raise even though the client always fails.
        run_extraction_job(store, None, _RaisingTaskClient(), "session:s1", "q", "a")
        assert store.list_facts("session:s1") == []

    def test_stores_extracted_facts(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        client = _StubTaskClient(
            json.dumps({"facts": [{"text": "is a data scientist", "confidence": 0.8}]})
        )
        run_extraction_job(store, None, client, "session:s1", "q", "a")
        facts = store.list_facts("session:s1")
        assert len(facts) == 1
        assert facts[0].text == "is a data scientist"

    def test_dedupes_against_existing_facts(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_fact("session:s1", "is a data scientist", confidence=0.8)
        client = _StubTaskClient(
            json.dumps({"facts": [{"text": "is a data scientist", "confidence": 0.9}]})
        )
        run_extraction_job(store, None, client, "session:s1", "q", "a")
        # Still just one -- the duplicate was not written.
        assert len(store.list_facts("session:s1")) == 1

    def test_no_facts_extracted_is_a_noop(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        client = _StubTaskClient(json.dumps({"facts": []}))
        run_extraction_job(store, None, client, "session:s1", "q", "a")
        assert store.list_facts("session:s1") == []
