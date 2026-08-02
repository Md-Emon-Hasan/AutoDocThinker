"""Tests for governance fail-mode behaviour: fail-closed vs fail-open.

Input guard always fails closed (a guard error rejects the request).
Output guard fails closed for high-risk domains, open-with-warning for
General. A guard crash must never become a 500.
"""

from unittest.mock import patch

from app.governance.input_guard import InputGuard
from app.governance.output_guard import OutputGuard


class TestInputGuardFailsClosed:
    def test_guard_error_rejects_request(self):
        guard = InputGuard()
        with patch(
            "app.governance.input_guard.check_size", side_effect=RuntimeError("boom")
        ):
            result = guard.check("anything")
        assert result.allowed is False
        assert "guard_error" in result.rules_fired


class TestOutputGuardFailModes:
    def test_high_risk_domain_fails_closed_on_error(self):
        guard = OutputGuard()
        with patch.object(OutputGuard, "_check", side_effect=RuntimeError("boom")):
            result = guard.check("answer", "medical", {"groundedness": 0.9})
        assert result.allowed is False
        assert "guard_error" in result.rules_fired

    def test_general_domain_fails_open_with_warning_on_error(self):
        guard = OutputGuard()
        with patch.object(OutputGuard, "_check", side_effect=RuntimeError("boom")):
            result = guard.check("answer", "general", {"groundedness": 0.9})
        assert result.allowed is True
        assert result.warning is not None

    def test_guard_crash_never_raises(self):
        guard = OutputGuard()
        with patch.object(OutputGuard, "_check", side_effect=RuntimeError("boom")):
            # Must not propagate -- this call must not raise.
            guard.check("answer", "legal", {"groundedness": 0.9})
