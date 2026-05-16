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


class TestChainFactory:
    def test_make_chain(self):
        mock_client = MagicMock()
        mock_client.answer.return_value = "chain result"
        chain = make_chain(lambda: "Prompt", mock_client)
        result = chain({"question": "q", "context": "ctx"})
        assert result == "chain result"
