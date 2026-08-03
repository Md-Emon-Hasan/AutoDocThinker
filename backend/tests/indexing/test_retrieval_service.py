"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.service import RetrievalService, hybrid_retrieve


class TestRetrievalService:
    def test_retrieve(self, populated_index):
        assert len(RetrievalService(populated_index).retrieve("alpha", 3)) >= 1

    def test_hybrid_retrieve(self, populated_index):
        assert len(hybrid_retrieve(populated_index, "alpha", 3)) >= 1
