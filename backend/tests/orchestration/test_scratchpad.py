"""Tests for app/orchestration/scratchpad.py::ScratchpadStore --
persistence, status tracking, survives restart."""

from app.orchestration.models import SubTask
from app.orchestration.scratchpad import ScratchpadStore


class TestScratchpadPersistence:
    def test_save_and_get(self, tmp_path):
        store = ScratchpadStore(tmp_path / "scratchpad.sqlite3")
        subtasks = [SubTask(id="t1", query="q1", depends_on=[])]
        store.save("query-1", "the question", subtasks)
        record = store.get("query-1")
        assert record["question"] == "the question"
        assert record["subtasks"][0]["id"] == "t1"
        assert record["statuses"]["t1"] == "pending"

    def test_update_status(self, tmp_path):
        store = ScratchpadStore(tmp_path / "scratchpad.sqlite3")
        store.save("query-1", "q", [SubTask(id="t1", query="q1", depends_on=[])])
        store.update_status("query-1", "t1", "done", note="all good")
        record = store.get("query-1")
        assert record["statuses"]["t1"] == "done"
        assert record["notes"]["t1"] == "all good"

    def test_get_unknown_query_returns_none(self, tmp_path):
        store = ScratchpadStore(tmp_path / "scratchpad.sqlite3")
        assert store.get("nonexistent") is None

    def test_survives_reopen(self, tmp_path):
        db_path = tmp_path / "scratchpad.sqlite3"
        ScratchpadStore(db_path).save(
            "query-1", "q", [SubTask(id="t1", query="q1", depends_on=[])]
        )
        reopened = ScratchpadStore(db_path)
        record = reopened.get("query-1")
        assert record is not None
        assert record["question"] == "q"

    def test_status_update_survives_reopen(self, tmp_path):
        db_path = tmp_path / "scratchpad.sqlite3"
        store = ScratchpadStore(db_path)
        store.save("query-1", "q", [SubTask(id="t1", query="q1", depends_on=[])])
        store.update_status("query-1", "t1", "failed", note="boom")

        reopened = ScratchpadStore(db_path)
        record = reopened.get("query-1")
        assert record["statuses"]["t1"] == "failed"
