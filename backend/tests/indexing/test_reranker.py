"""Consolidated tests for indexing and retrieval modules."""

from app.ingestion.document import Document
from app.retrieval.reranker import rerank_documents


class TestReranker:
    def test_reranks(self):
        docs = [Document("alpha beta", {}), Document("gamma delta", {})]
        assert rerank_documents("alpha", docs, 2)[0].page_content == "alpha beta"

    def test_empty(self):
        assert rerank_documents("q", [], 5) == []
