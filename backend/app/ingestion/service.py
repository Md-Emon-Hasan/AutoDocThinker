import logging
from pathlib import Path
from typing import Any, cast

from app.ingestion.chunk_optimizer import ChunkOptimizer
from app.ingestion.document_processor import DocumentProcessor
from app.ingestion.supported_types import extension_to_type

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        index,
        processor: DocumentProcessor | None = None,
        optimizer: ChunkOptimizer | None = None,
        dense_index=None,
    ) -> None:
        self.index = index
        self.processor = processor or DocumentProcessor()
        self.optimizer = optimizer or ChunkOptimizer()
        self.dense_index = dense_index

    def ingest(
        self, source: str, file_type: str, display_name: str | None = None
    ) -> dict:
        docs = self.processor.load(source, file_type, display_name=display_name)
        chunks = self.optimizer.split(docs, file_type)
        added = self.index.add(chunks)
        if self.dense_index is not None and added:
            # Best-effort: a dense-store hiccup must not break ingestion,
            # which today is sparse-index-only behavior that many existing
            # tests depend on.
            try:
                self.dense_index.add(chunks)
            except Exception:
                logger.exception(
                    "Dense index write failed for source=%s; continuing with "
                    "sparse-only ingestion",
                    source,
                )
        return {
            "chunks_added": added,
            "total_chunks": self.index.size,
            "sources": self.index.sources,
        }

    def auto_ingest(self, data_dir: Path, extensions: tuple[str, ...]) -> dict:
        summary: dict[str, list[Any]] = {"ingested": [], "skipped": [], "failed": []}
        for path in sorted(data_dir.iterdir()) if data_dir.exists() else []:
            file_type = extension_to_type(path.suffix)
            if (
                not path.is_file()
                or path.suffix.lower() not in extensions
                or not file_type
            ):
                continue
            try:
                result = self.ingest(str(path), file_type)
                bucket = "ingested" if result["chunks_added"] else "skipped"
                summary[bucket].append(path.name)
            except Exception as exc:
                summary["failed"].append({"file": path.name, "error": str(exc)})
        return summary


def ingest_documents(index, file_path: str, file_type: str) -> int:
    return cast(
        int, IngestionService(index).ingest(file_path, file_type)["chunks_added"]
    )


def ingest_file(index, file_path: str, file_type: str) -> dict:
    return IngestionService(index).ingest(file_path, file_type)


def auto_ingest_data_dir(index, data_dir: Path, extensions: tuple[str, ...]) -> dict:
    return IngestionService(index).auto_ingest(data_dir, extensions)
