"""Consolidated tests for LLM module and prompts."""

from app.ingestion.document import Document
from app.llm.wikipedia_client import WikipediaClient


class TestWikipedia:
    def test_search(self):
        doc = WikipediaClient().search("alpha")
        assert isinstance(doc, Document)
        assert doc.metadata["source"] == "Wikipedia"
