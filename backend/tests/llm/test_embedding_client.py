"""Consolidated tests for LLM module and prompts."""

from app.llm.embedding_client import EmbeddingClient


class TestEmbeddingClient:
    def test_embed(self):
        assert EmbeddingClient().embed("abc") == [3.0]
