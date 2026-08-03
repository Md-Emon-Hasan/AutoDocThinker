"""Consolidated tests for LLM module and prompts."""

from unittest.mock import MagicMock, patch

import pytest

from app.llm.groq_client import GroqClient


class TestGroqClient:
    def test_answer_with_context(self):
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test answer"
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        with patch("app.llm.groq_client.Groq", mock_groq):
            client = GroqClient()
            answer = client.answer("q", "ctx", "Prompt")
            assert answer == "test answer"

    def test_answer_without_context(self):
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "general answer"
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        with patch("app.llm.groq_client.Groq", mock_groq):
            client = GroqClient()
            answer = client.answer("q", "", "Prompt")
            assert answer == "general answer"

    def test_rate_limit_error(self):
        from groq import RateLimitError as GroqRateLimitError

        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        err = GroqRateLimitError("rate limit", response=mock_response, body={})
        mock_groq.return_value.chat.completions.create.side_effect = err

        with patch("app.llm.groq_client.Groq", mock_groq):
            client = GroqClient()
            with pytest.raises(RuntimeError, match="rate limit reached"):
                client.answer("q", "ctx", "prompt")
