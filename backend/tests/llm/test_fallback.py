"""Consolidated tests for LLM module and prompts."""

from app.llm.fallback import fallback_answer


class TestFallback:
    def test_includes_question(self):
        assert "q" in fallback_answer("q")
