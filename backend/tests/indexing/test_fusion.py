"""Consolidated tests for indexing and retrieval modules."""

from app.ingestion.document import Document
from app.retrieval.fusion import reciprocal_rank_fusion


class TestFusion:
    def test_deduplicates(self):
        d = Document("text", {"chunk_id": "c1"})
        assert len(reciprocal_rank_fusion([[d], [d]], 5)) == 1
