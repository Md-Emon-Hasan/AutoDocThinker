from datetime import UTC, datetime
from pathlib import Path

from app.ingestion.loaders.factory import get_loader
from app.ingestion.source_id import make_source_id


class DocumentProcessor:
    def load(self, source: str, file_type: str, display_name: str | None = None):
        docs = get_loader(file_type).load(source)
        if not docs:
            raise ValueError("Loader returned no documents")

        if display_name:
            source_name = display_name
        elif file_type == "url":
            source_name = source
        elif file_type == "text":
            source_name = "pasted_text"
        else:
            source_name = Path(source).name

        source_id = make_source_id(source)
        timestamp = datetime.now(UTC).isoformat()
        for index, doc in enumerate(docs):
            doc.metadata = {
                **doc.metadata,
                "source": source_name,
                "source_id": source_id,
                "file_type": file_type,
                "doc_index": index,
                "ingested_at": timestamp,
            }
        return docs
