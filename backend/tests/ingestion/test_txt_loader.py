"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.loaders.txt_loader import TxtLoader


class TestTxtLoader:
    def test_load_from_file(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("Test content", encoding="utf-8")
        assert TxtLoader().load(str(f))[0].page_content == "Test content"
