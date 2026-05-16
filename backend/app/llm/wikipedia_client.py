from app.ingestion.document import Document


class WikipediaClient:
    def search(self, query: str) -> Document:
        return Document(
            f"Wikipedia fallback summary for {query}",
            {"source": "Wikipedia", "source_id": "wikipedia", "file_type": "web"},
        )
