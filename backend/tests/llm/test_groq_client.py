"""Consolidated tests for LLM module and prompts."""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.document import Document
from app.llm.chain_factory import make_chain
from app.llm.embedding_client import EmbeddingClient
from app.llm.fallback import fallback_answer
from app.llm.groq_client import GroqClient
from app.llm.output_parser import parse_text
from app.llm.wikipedia_client import WikipediaClient
from app.prompts.answer import answer_instruction
from app.prompts.base import domain_system_prompt
from app.prompts.compression import compression_instruction
from app.prompts.crag import crag_instruction
from app.prompts.domain import GENERAL_PROMPT
from app.prompts.domain.customer_support import CUSTOMER_SUPPORT_PROMPT
from app.prompts.domain.education import EDUCATION_PROMPT
from app.prompts.domain.finance import FINANCE_PROMPT
from app.prompts.domain.legal import LEGAL_PROMPT
from app.prompts.domain.medical import MEDICAL_PROMPT
from app.prompts.domain.technical import TECHNICAL_PROMPT
from app.prompts.evaluation import confidence_instruction
from app.prompts.query_rewrite import rewrite_queries
from app.prompts.self_rag import self_rag_instruction


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
