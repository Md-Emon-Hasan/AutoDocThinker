"""Pending items survive a simulated restart (new HITLStore instance
pointed at the same SQLite file)."""

from app.hitl.store import HITLStore


class TestPersistence:
    def test_pending_item_survives_reopen(self, tmp_path):
        db_path = tmp_path / "hitl.sqlite3"
        store = HITLStore(db_path)
        item = store.create(
            "low_groundedness_answer",
            "reason",
            {"answer": "x"},
            "session:a",
            ttl_seconds=None,
        )

        # Simulate a process restart: a brand-new HITLStore instance
        # over the same file must see the same pending item.
        reopened = HITLStore(db_path)
        found = reopened.get(item.id)
        assert found is not None
        assert found.status == "pending"
        assert found.proposed_output == {"answer": "x"}

    def test_decision_survives_reopen(self, tmp_path):
        db_path = tmp_path / "hitl.sqlite3"
        store = HITLStore(db_path)
        item = store.create(
            "kind", "reason", {"answer": "x"}, "session:a", ttl_seconds=None
        )
        store.approve(item.id, reason="looks fine")

        reopened = HITLStore(db_path)
        found = reopened.get(item.id)
        assert found.status == "approved"
        assert found.decision_reason == "looks fine"

    def test_list_pending_survives_reopen(self, tmp_path):
        db_path = tmp_path / "hitl.sqlite3"
        store = HITLStore(db_path)
        store.create("kind", "reason", {"a": 1}, "session:a", ttl_seconds=None)
        store.create("kind", "reason", {"a": 2}, "session:b", ttl_seconds=None)

        reopened = HITLStore(db_path)
        result = reopened.list_pending()
        assert result["total"] == 2
