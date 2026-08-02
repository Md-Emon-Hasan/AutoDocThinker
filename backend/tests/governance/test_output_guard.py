"""Tests for app/governance/output_guard.py."""

from app.governance.output_guard import OutputGuard


class TestOutputGuard:
    def test_pii_leakage_caught(self):
        result = OutputGuard().check("contact jane@example.com", "general", None)
        assert "pii_leakage" in result.rules_fired
        assert result.redacted_text is not None
        assert "jane@example.com" not in result.redacted_text

    def test_general_domain_open_with_warning_on_ungrounded(self):
        result = OutputGuard().check(
            "A confident claim.", "general", {"groundedness": 0.1}
        )
        assert result.allowed is True
        assert "ungrounded_assertion" in result.rules_fired
        assert result.warning is not None

    def test_medical_domain_fails_closed_on_ungrounded(self):
        result = OutputGuard().check(
            "You should take this medication.", "medical", {"groundedness": 0.2}
        )
        assert result.allowed is False

    def test_legal_domain_fails_closed_on_missing_disclaimer(self):
        result = OutputGuard().check(
            "You will definitely win this case.", "legal", {"groundedness": 0.9}
        )
        assert result.allowed is False
        assert "missing_disclaimer_or_hedging" in result.rules_fired

    def test_legal_domain_allowed_with_disclaimer(self):
        result = OutputGuard().check(
            "This is not legal advice; consult a lawyer for specifics.",
            "legal",
            {"groundedness": 0.9},
        )
        assert result.allowed is True

    def test_finance_domain_fails_closed_on_ungrounded(self):
        result = OutputGuard().check(
            "Buy this stock now.", "finance", {"groundedness": 0.1}
        )
        assert result.allowed is False

    def test_no_verification_result_skips_groundedness_check(self):
        result = OutputGuard().check(
            "Some hedged answer, generally speaking.", "general", None
        )
        assert "ungrounded_assertion" not in result.rules_fired

    def test_consumes_verifier_result_without_new_llm_call(self):
        # OutputGuard.check takes verification as a plain dict -- no
        # gateway/task_client dependency exists on the class at all.
        assert not hasattr(OutputGuard(), "task_client")
        assert not hasattr(OutputGuard(), "gateway")

    def test_high_risk_domain_grounded_with_disclaimer_allowed(self):
        result = OutputGuard().check(
            "Generally, this may apply -- consult a doctor for advice.",
            "medical",
            {"groundedness": 0.9},
        )
        assert result.allowed is True
        assert result.rules_fired == []
