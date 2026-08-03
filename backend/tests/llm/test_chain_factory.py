"""Consolidated tests for LLM module and prompts."""

from unittest.mock import MagicMock

from app.llm.chain_factory import make_chain


class TestChainFactory:
    def test_make_chain(self):
        mock_client = MagicMock()
        mock_client.answer.return_value = "chain result"
        chain = make_chain(lambda: "Prompt", mock_client)
        result = chain({"question": "q", "context": "ctx"})
        assert result == "chain result"
