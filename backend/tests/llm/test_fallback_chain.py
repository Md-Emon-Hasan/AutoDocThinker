"""Tests for app/llm/gateway/fallback.py: the ordered provider chain."""

from unittest.mock import patch

import pytest

from app.llm.gateway.fallback import is_retryable, with_fallback
from app.llm.gateway.models import GatewayRequest, TaskCategory


def _request() -> GatewayRequest:
    return GatewayRequest(
        question="what is the payment term?",
        context="ctx",
        domain_prompt="prompt",
        task=TaskCategory.ANSWER_GENERATION,
    )


class _FailingProvider:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc
        self.calls = 0

    def answer(self, question, context, domain_prompt) -> str:
        self.calls += 1
        raise self._exc


class _WorkingProvider:
    def __init__(self, response: str = "ok") -> None:
        self._response = response
        self.calls = 0

    def answer(self, question, context, domain_prompt) -> str:
        self.calls += 1
        return self._response


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("app.llm.gateway.fallback.time.sleep") as mock_sleep:
        yield mock_sleep


class TestIsRetryable:
    def test_timeout_is_retryable(self):
        assert is_retryable(TimeoutError("timed out"))

    def test_connection_error_is_retryable(self):
        assert is_retryable(ConnectionError("connection refused"))

    def test_rate_limit_message_is_retryable(self):
        assert is_retryable(RuntimeError("Groq API rate limit reached"))

    def test_5xx_message_is_retryable(self):
        assert is_retryable(RuntimeError("upstream returned 503"))

    def test_400_message_is_not_retryable(self):
        assert not is_retryable(RuntimeError("400 bad request"))

    def test_auth_failure_is_not_retryable(self):
        assert not is_retryable(RuntimeError("invalid api key: unauthorized"))

    def test_value_error_is_not_retryable(self):
        assert not is_retryable(ValueError("bad input"))

    def test_unrecognized_message_defaults_non_retryable(self):
        assert not is_retryable(RuntimeError("something completely unexpected"))


class TestWithFallback:
    def test_retryable_failures_advance_chain_to_working_provider(self, _no_sleep):
        failing = _FailingProvider(RuntimeError("503 service unavailable"))
        working = _WorkingProvider("answer from second provider")

        response = with_fallback([failing, working], _request(), max_attempts=2)

        assert response.text == "answer from second provider"
        assert response.provider == "_WorkingProvider"

    def test_non_retryable_failure_does_not_retry_same_provider(self):
        failing = _FailingProvider(RuntimeError("400 bad request"))
        working = _WorkingProvider()

        with_fallback([failing, working], _request(), max_attempts=5)

        # No same-provider retry burning quota on a request that will
        # fail identically every time.
        assert failing.calls == 1

    def test_same_provider_retries_respect_max_attempts(self, _no_sleep):
        failing = _FailingProvider(RuntimeError("connection reset"))

        with_fallback([failing], _request(), max_attempts=3)

        assert failing.calls == 3

    def test_backoff_sleep_called_between_same_provider_retries(self, _no_sleep):
        failing = _FailingProvider(RuntimeError("timeout"))

        with_fallback([failing], _request(), max_attempts=3)

        # Sleeps between attempts, not after the last exhausted attempt.
        assert _no_sleep.call_count == 2

    def test_full_exhaustion_returns_fallback_answer_not_raise(self):
        failing = _FailingProvider(RuntimeError("connection reset"))

        response = with_fallback([failing], _request(), max_attempts=1)

        assert "payment term" in response.text
        assert response.provider == "fallback"

    def test_empty_provider_list_returns_fallback_answer(self):
        response = with_fallback([], _request(), max_attempts=1)

        assert response.provider == "fallback"
