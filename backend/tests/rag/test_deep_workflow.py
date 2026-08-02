"""`deep` is registered as a fifth mode; the original four modes behave
identically to before (regression check)."""

import json

from app.orchestration.orchestrator import DeepOrchestrator
from app.rag.modes import RAG_MODES, ensure_mode
from app.rag.service import RAGService
from app.workflows.deep import run_deep


class _FakeProfile:
    system_prompt = "system prompt"
    name = "general"
    metadata_filter = {}


class _FakeDomains:
    def get(self, name):
        return _FakeProfile()


class _FakeRetrieval:
    class _Index:
        version = 1

    index = _Index()

    def retrieve(self, query, k, metadata_filter=None):
        return []


class _PlannerClient:
    def answer(self, question, context, domain_prompt):
        return json.dumps(
            {"subtasks": [{"id": "t1", "query": question, "depends_on": []}]}
        )


class _StubLLM:
    model_name = "test-model"

    def answer(self, question, context, domain_prompt):
        return "an answer [1]" if "Synthesize" in domain_prompt else "sub-answer"


class TestDeepModeRegistered:
    def test_deep_in_rag_modes(self):
        assert "deep" in RAG_MODES

    def test_ensure_mode_accepts_deep(self):
        assert ensure_mode("deep") == "deep"

    def test_ensure_mode_still_rejects_unknown(self):
        import pytest

        with pytest.raises(ValueError):
            ensure_mode("not-a-real-mode")


class TestDeepModeEndToEnd:
    def test_run_deep_produces_answer_via_orchestrator(self):
        orchestrator = DeepOrchestrator(
            _FakeRetrieval(),
            _StubLLM(),
            _PlannerClient(),
            concurrency=2,
            query_timeout_seconds=10.0,
            max_llm_calls=20,
            max_tokens=50_000,
            max_wall_clock_seconds=30.0,
            max_recursion_depth=1,
            max_subtasks=5,
            max_plan_depth=2,
        )
        state = {
            "input": "a sufficiently long non-trivial question and another clause",
            "formatter": None,
            "metadata_filter": None,
        }
        result = run_deep(
            state, _FakeRetrieval(), _StubLLM(), _FakeProfile(), orchestrator
        )
        assert result["answer"]
        assert "orchestration" not in result or isinstance(result.get("sources"), list)

    def test_rag_service_query_dispatches_deep_mode(self):
        orchestrator = DeepOrchestrator(
            _FakeRetrieval(),
            _StubLLM(),
            _PlannerClient(),
            concurrency=2,
            query_timeout_seconds=10.0,
            max_llm_calls=20,
            max_tokens=50_000,
            max_wall_clock_seconds=30.0,
            max_recursion_depth=1,
            max_subtasks=5,
            max_plan_depth=2,
        )
        rag = RAGService(
            _FakeDomains(),
            _FakeRetrieval(),
            _StubLLM(),
            wiki=None,
            orchestrator=orchestrator,
        )
        response = rag.query(
            "a sufficiently long non-trivial question and another clause",
            "general",
            "deep",
        )
        assert response["mode"] == "deep"
        assert response["answer"]
        assert "orchestration" in response["metadata"]
        assert "budget" in response["metadata"]["orchestration"]


class TestOriginalFourModesUnaffected:
    """Regression: the four pre-Stage-6 modes behave identically."""

    def test_naive_still_dispatches(self, seeded_container):
        box = seeded_container
        response = box["rag"].query("payment terms", "general", "naive")
        assert response["mode"] == "naive"
        assert response["answer"]

    def test_advanced_still_dispatches(self, seeded_container):
        box = seeded_container
        response = box["rag"].query("payment terms", "general", "advanced")
        assert response["mode"] == "advanced"
        assert response["answer"]

    def test_crag_still_dispatches(self, seeded_container):
        box = seeded_container
        response = box["rag"].query("payment terms", "general", "crag")
        assert response["mode"] == "crag"
        assert response["answer"]

    def test_self_rag_still_dispatches(self, seeded_container):
        box = seeded_container
        response = box["rag"].query("payment terms", "general", "self_rag")
        assert response["mode"] == "self_rag"
        assert response["answer"]
