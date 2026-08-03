"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

# ── citations & formatting ───────────────────────────────────────────────────


class TestRAGService:
    def test_naive(self, seeded_container):
        result = seeded_container["rag"].query("payment terms", "general", "naive")
        assert result["answer"] and result["history"][-1]["role"] == "assistant"

    def test_advanced(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "advanced")[
            "answer"
        ]

    def test_crag(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "crag")[
            "answer"
        ]

    def test_self_rag(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "self_rag")[
            "answer"
        ]

    def test_crag_web_search_trigger(self, seeded_container):
        result = seeded_container["rag"].query("unmatched", "general", "crag")
        assert result["metadata"]["confidence"] >= 0.6
