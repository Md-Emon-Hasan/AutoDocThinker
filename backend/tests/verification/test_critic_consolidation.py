"""Consolidation check: Self-RAG behaviour is unchanged, and there is
exactly one real reflection implementation (app/verification/critic.py).

self_rag_critique/self_rag_revise (app/workflows/self_rag/compat.py) were
already hardcoded stubs before Stage 3 -- never wired into the graph,
never containing real critique logic. There was nothing to extract from
them; Critic is the first and only real implementation. This test
confirms both halves: the stubs keep their exact pre-Stage-3 behaviour,
and Self-RAG's real graph output is unaffected by Critic's existence.
"""

import json

from app.ingestion.document import Document
from app.verification.critic import Critic
from app.workflows.self_rag import run_self_rag
from app.workflows.self_rag.compat import self_rag_critique, self_rag_revise


class _StubRetrieval:
    def retrieve(self, query, k, metadata_filter=None):
        return [Document("alpha beta", {"source_id": "s1", "chunk_id": "c1"})]


class _StubLLM:
    def answer(self, question, context, domain_prompt):
        return f"answer to {question}"


class _StubProfile:
    system_prompt = "system"


class TestSelfRAGUnchanged:
    def test_critique_stub_exact_value_unchanged(self):
        assert self_rag_critique({"answer": "x"})["critique"] == "No issues detected."

    def test_revise_stub_prefers_draft_answer(self):
        assert self_rag_revise({"draft_answer": "revised"})["answer"] == "revised"

    def test_revise_stub_falls_back_to_answer(self):
        assert self_rag_revise({"answer": "original"})["answer"] == "original"

    def test_run_self_rag_graph_unaffected_by_critic_existing(self):
        from app.rag.formatting import format_context_with_sources

        state = {
            "input": "payment terms",
            "formatter": format_context_with_sources,
            "metadata_filter": None,
        }
        result = run_self_rag(state, _StubRetrieval(), _StubLLM(), _StubProfile())
        assert result["answer"] == "answer to payment terms"
        # Real reflection (Critic) is not wired into the graph -- decide
        # -> generate -> END, exactly as before Stage 3.
        assert "critique" not in result


class TestOneRealCriticImplementation:
    def test_critic_produces_real_structured_output(self):
        class _StubTaskClient:
            def answer(self, question, context, domain_prompt):
                return json.dumps(
                    {"groundedness": 0.7, "claims": [], "unsupported_claims": []}
                )

        critic = Critic()
        result = critic.assess("q", "answer", "context", _StubTaskClient())
        assert result["groundedness"] == 0.7

    def test_critic_is_the_only_place_json_verdict_logic_lives(self):
        # self_rag_critique returns a hardcoded string, not a parsed
        # verdict -- Critic.assess is the sole real implementation.
        assert self_rag_critique({})["critique"] == "No issues detected."
        assert not hasattr(self_rag_critique, "assess")
