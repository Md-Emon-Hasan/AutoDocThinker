"""Tests for app/rag/streaming.py::stream_query -- token streaming
through the llm, node events for all five modes, budget events in deep
mode."""

import json

from app.domain.registry import DomainRegistry
from app.indexing.hybrid_index import HybridIndex
from app.ingestion.document import Document
from app.llm.wikipedia_client import WikipediaClient
from app.orchestration.orchestrator import DeepOrchestrator
from app.rag.service import RAGService
from app.rag.streaming import stream_query
from app.retrieval.service import RetrievalService


class _StubLLM:
    model_name = "test-model"

    def answer(self, question, context, domain_prompt):
        if "Synthesize" in domain_prompt:
            return "synthesized [1]"
        return "an answer about the document"


class _PlannerClient:
    def answer(self, question, context, domain_prompt):
        return json.dumps(
            {"subtasks": [{"id": "t1", "query": question, "depends_on": []}]}
        )


def _make_rag_service(mode_extra_kwargs=None):
    index = HybridIndex()
    index.add(
        [
            Document(
                "payment terms are net thirty days",
                {"source_id": "s1", "chunk_id": "c1"},
            )
        ]
    )
    retrieval = RetrievalService(index)
    domains = DomainRegistry()
    kwargs = dict(mode_extra_kwargs or {})
    return RAGService(domains, retrieval, _StubLLM(), wiki=WikipediaClient(), **kwargs)


def _collect(gen):
    return list(gen)


class TestEventOrderNaive:
    def test_events_in_expected_order(self):
        rag = _make_rag_service()
        events = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: False
            )
        )
        types = [e["event"] for e in events]
        assert types[0] == "node_start"
        assert "node_end" in types
        assert "retrieval_result" in types
        assert "citation" in types
        assert "token" in types
        assert types[-1] == "done"
        # citations must precede tokens (order matters for the UI)
        assert types.index("citation") < types.index("token")

    def test_final_done_event_contains_full_answer(self):
        rag = _make_rag_service()
        events = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: False
            )
        )
        done = events[-1]
        assert done["event"] == "done"
        assert done["data"]["response"]["answer"]

    def test_tokens_reconstruct_full_answer(self):
        rag = _make_rag_service()
        events = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: False
            )
        )
        tokens = "".join(e["data"]["text"] for e in events if e["event"] == "token")
        done_answer = events[-1]["data"]["response"]["answer"]
        assert tokens == done_answer


class TestAllFiveModes:
    def _run(self, mode):
        rag = _make_rag_service()
        events = _collect(
            stream_query(
                rag, "payment terms", "general", mode, [], None, None, lambda: False
            )
        )
        node_names = [
            e["data"]["node"]
            for e in events
            if e["event"] in ("node_start", "node_end")
        ]
        assert any(mode in n for n in node_names)
        assert events[-1]["event"] == "done"

    def test_naive(self):
        self._run("naive")

    def test_advanced(self):
        self._run("advanced")

    def test_crag(self):
        self._run("crag")

    def test_self_rag(self):
        self._run("self_rag")

    def test_deep_emits_budget_status(self):
        orchestrator = DeepOrchestrator(
            RetrievalService(HybridIndex()),
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
        rag = _make_rag_service({"orchestrator": orchestrator})
        events = _collect(
            stream_query(
                rag,
                "a sufficiently long non-trivial question and another clause here",
                "general",
                "deep",
                [],
                None,
                None,
                lambda: False,
            )
        )
        assert any(e["event"] == "budget_status" for e in events)


class TestCacheHitStreams:
    def test_second_identical_query_is_a_cache_hit(self):
        from app.core.config import RAGConfig
        from app.utils.cache import CacheManager

        cache_manager = CacheManager.from_config(RAGConfig())
        rag = _make_rag_service({"cache_manager": cache_manager})

        first = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: False
            )
        )
        assert "cache_hit" not in [e["event"] for e in first]

        second = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: False
            )
        )
        types = [e["event"] for e in second]
        assert "cache_hit" in types
        assert "token" in types
        assert types[-1] == "done"


class TestDisconnectCancelsWorkflow:
    def test_is_cancelled_stops_before_dispatch(self):
        rag = _make_rag_service()
        events = _collect(
            stream_query(
                rag, "payment terms", "general", "naive", [], None, None, lambda: True
            )
        )
        types = [e["event"] for e in events]
        assert "error" in types
        # Must stop before ever dispatching the mode / calling the LLM.
        assert not any(
            "dispatch" in e["data"].get("node", "")
            for e in events
            if e["event"] == "node_start"
        )
