"""Consolidated tests for LLM module and prompts."""

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


class TestPrompts:
    def test_domain_system_prompt(self):
        assert "cite" in domain_system_prompt("x").lower()

    def test_answer_instruction(self):
        assert answer_instruction()

    def test_compression_instruction(self):
        assert "10" in compression_instruction(10)

    def test_confidence_instruction(self):
        assert confidence_instruction()

    def test_crag_instruction(self):
        assert crag_instruction()

    def test_self_rag_instruction(self):
        assert self_rag_instruction()

    def test_rewrite_queries(self):
        result = rewrite_queries("q", "Legal")
        assert result == ["q", "Legal: q"]

    def test_all_domain_prompts(self):
        for p in (
            GENERAL_PROMPT,
            CUSTOMER_SUPPORT_PROMPT,
            EDUCATION_PROMPT,
            FINANCE_PROMPT,
            LEGAL_PROMPT,
            MEDICAL_PROMPT,
            TECHNICAL_PROMPT,
        ):
            assert isinstance(p, str) and len(p) > 0
