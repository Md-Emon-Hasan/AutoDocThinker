"""Tests for app/hitl/gate.py::HITLGate -- gating per config, off by
default, approve/reject/edit, expiry defaults to reject."""

from app.core.config import RAGConfig
from app.hitl.gate import HITLGate
from app.hitl.store import HITLStore


def _gate(tmp_path, **overrides) -> HITLGate:
    store = HITLStore(tmp_path / "hitl.sqlite3")
    config = RAGConfig(**overrides)
    return HITLGate(store, config)


class TestGatingOffByDefault:
    def test_disabled_by_default_never_gates(self, tmp_path):
        gate = _gate(tmp_path)  # hitl_enabled defaults to False
        assert gate.enabled is False
        gated, kind = gate.should_gate_answer("legal", {"groundedness": 0.0})
        assert gated is False
        assert kind is None
        assert gate.should_gate_destructive_op() is False


class TestGatingPerConfig:
    def test_low_groundedness_gates_when_enabled(self, tmp_path):
        gate = _gate(
            tmp_path,
            hitl_enabled=True,
            hitl_gate_low_groundedness=True,
            hitl_gate_high_risk_domains=False,
            verification_min_groundedness=0.5,
        )
        gated, kind = gate.should_gate_answer("general", {"groundedness": 0.2})
        assert gated is True
        assert kind == "low_groundedness_answer"

    def test_high_groundedness_not_gated(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True, verification_min_groundedness=0.5)
        gated, kind = gate.should_gate_answer("general", {"groundedness": 0.9})
        assert gated is False

    def test_high_risk_domain_low_confidence_gates(self, tmp_path):
        gate = _gate(
            tmp_path,
            hitl_enabled=True,
            hitl_gate_low_groundedness=False,
            hitl_gate_high_risk_domains=True,
            verification_min_groundedness=0.5,
        )
        gated, kind = gate.should_gate_answer("medical", {"groundedness": 0.1})
        assert gated is True
        assert kind == "high_risk_low_confidence_answer"

    def test_destructive_ops_gated_when_configured(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True, hitl_gate_destructive_ops=True)
        assert gate.should_gate_destructive_op() is True

    def test_destructive_ops_not_gated_when_disabled(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True, hitl_gate_destructive_ops=False)
        assert gate.should_gate_destructive_op() is False


class TestApproveRejectEdit:
    def test_approve_returns_proposed_output(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True)
        pending = gate.create_pending("kind", "reason", {"answer": "x"}, "session:a")
        approved = gate.store.approve(pending["id"])
        assert approved.status == "approved"
        assert approved.final_output == {"answer": "x"}

    def test_reject_records_reason(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True)
        pending = gate.create_pending("kind", "reason", {"answer": "x"}, "session:a")
        rejected = gate.store.reject(pending["id"], reason="not accurate")
        assert rejected.status == "rejected"
        assert rejected.decision_reason == "not accurate"
        assert rejected.final_output is None

    def test_edit_and_approve_overrides_output(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True)
        pending = gate.create_pending("kind", "reason", {"answer": "x"}, "session:a")
        edited = gate.store.edit_and_approve(pending["id"], {"answer": "corrected"})
        assert edited.status == "approved"
        assert edited.final_output == {"answer": "corrected"}


class TestExpiry:
    def test_expiry_defaults_to_reject(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True, hitl_expiry_default_action="reject")
        pending = gate.store.create(
            "kind", "reason", {"answer": "x"}, "session:a", ttl_seconds=1, now=0.0
        )
        expired_count = gate.store.expire_stale(
            default_action=gate.config.hitl_expiry_default_action, now=100.0
        )
        assert expired_count == 1
        item = gate.store.get(pending.id)
        assert item.status == "rejected"

    def test_not_yet_expired_stays_pending(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True)
        pending = gate.store.create(
            "kind", "reason", {"answer": "x"}, "session:a", ttl_seconds=1000, now=0.0
        )
        gate.store.expire_stale(now=1.0)
        item = gate.store.get(pending.id)
        assert item.status == "pending"


class TestGatedRequestReturnsPendingIdImmediately:
    def test_create_pending_returns_id_not_a_blocking_wait(self, tmp_path):
        gate = _gate(tmp_path, hitl_enabled=True)
        pending = gate.create_pending("kind", "reason", {"answer": "x"}, "session:a")
        assert "id" in pending
        assert pending["status"] == "pending"
