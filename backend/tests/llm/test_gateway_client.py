"""Tests for the LLM gateway façade: app/llm/gateway/client.py."""

from unittest.mock import MagicMock

import pytest

from app.core.config import RAGConfig
from app.dependencies import container
from app.llm.gateway.client import LLMGateway, TaskBoundClient
from app.llm.gateway.models import TaskCategory
from app.llm.groq_client import GroqClient


class _StubProvider:
    def __init__(self, response: str = "stub answer") -> None:
        self._response = response

    def answer(self, question: str, context: str, domain_prompt: str) -> str:
        return self._response


class TestLLMGateway:
    def test_answer_uses_configured_provider(self):
        gateway = LLMGateway(
            providers_by_task={
                TaskCategory.ANSWER_GENERATION: [_StubProvider("hello")]
            },
            config=RAGConfig(),
        )
        result = gateway.answer("q", "ctx", "prompt", TaskCategory.ANSWER_GENERATION)
        assert result == "hello"

    def test_unknown_task_falls_back_to_canned_answer(self):
        gateway = LLMGateway(providers_by_task={}, config=RAGConfig())
        result = gateway.answer("my question", "", "prompt", TaskCategory.VERIFICATION)
        assert "my question" in result


class TestTaskBoundClient:
    def test_matches_groq_client_answer_signature(self):
        gateway = MagicMock(spec=LLMGateway)
        gateway.answer.return_value = "bound answer"
        client = TaskBoundClient(gateway, TaskCategory.ANSWER_GENERATION)

        # Same 3-positional-arg call chain_factory.py/nodes.py already use.
        result = client.answer("question", "context", "domain prompt")

        assert result == "bound answer"
        gateway.answer.assert_called_once_with(
            "question", "context", "domain prompt", TaskCategory.ANSWER_GENERATION
        )

    def test_duck_types_as_groq_client_replacement(self):
        import inspect

        assert inspect.signature(TaskBoundClient.answer).parameters.keys() == (
            inspect.signature(GroqClient.answer).parameters.keys()
        )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)


class TestGatewayEnabledFlag:
    def test_disabled_flag_injects_raw_groq_client(self, monkeypatch):
        """LLM_GATEWAY_ENABLED=false must yield the exact pre-Stage-1
        direct-GroqClient object, not a gateway-wrapped one -- this is
        the reversibility guarantee."""
        monkeypatch.setenv("LLM_GATEWAY_ENABLED", "false")
        container.cache_clear()
        try:
            box = container()
            assert type(box["rag"].llm).__name__ == "_FakeGroqClient"
        finally:
            container.cache_clear()

    def test_enabled_by_default_injects_task_bound_client(self, monkeypatch):
        monkeypatch.delenv("LLM_GATEWAY_ENABLED", raising=False)
        container.cache_clear()
        try:
            box = container()
            assert isinstance(box["rag"].llm, TaskBoundClient)
        finally:
            container.cache_clear()
