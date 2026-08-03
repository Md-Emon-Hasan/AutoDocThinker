"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.indexing.hybrid_index import HybridIndex
from app.ingestion.service import (
    auto_ingest_data_dir,
    ingest_documents,
    ingest_file,
)


class TestStandaloneFunctions:
    def test_ingest_documents(self, tmp_path):
        f = tmp_path / "other.txt"
        f.write_text("new source alpha", encoding="utf-8")
        assert ingest_documents(HybridIndex(), str(f), "txt") >= 1

    def test_ingest_file(self, tmp_path):
        f = tmp_path / "other.txt"
        f.write_text("new source alpha", encoding="utf-8")
        idx = HybridIndex()
        ingest_documents(idx, str(f), "txt")
        assert ingest_file(idx, str(f), "txt")["chunks_added"] == 0

    def test_auto_ingest_data_dir(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.txt").write_text("hello world", encoding="utf-8")
        assert auto_ingest_data_dir(HybridIndex(), data, (".txt",))["ingested"] == [
            "a.txt"
        ]
