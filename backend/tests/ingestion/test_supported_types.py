"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.supported_types import extension_to_type


class TestSupportedTypes:
    def test_txt(self):
        assert extension_to_type(".TXT") == "txt"

    def test_pdf(self):
        assert extension_to_type(".pdf") == "pdf"

    def test_docx(self):
        assert extension_to_type(".docx") == "docx"

    def test_unknown(self):
        assert extension_to_type(".bad") is None
