"""Consolidated tests for LLM module and prompts."""

from app.llm.output_parser import parse_text


class TestOutputParser:
    def test_strips(self):
        assert parse_text(" hi ") == "hi"

    def test_non_string(self):
        assert parse_text(42) == "42"
