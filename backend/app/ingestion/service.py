import logging
from pathlib import Path
from typing import Any, cast

from app.governance.input_guard import validate_url
from app.ingestion.chunk_optimizer import ChunkOptimizer
from app.ingestion.document_processor import DocumentProcessor
from app.ingestion.supported_types import extension_to_type
from app.retrieval.filters import SHARED_SCOPE, resolve_scope

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
        self,
        source: str,
        file_type: str,
        display_name: str | None = None,
        scope: str | None = None,
    ) -> dict:
        """Ingest ``source``, scoping every chunk to ``scope``.

        When ``scope`` is omitted, resolves to ANONYMOUS_SCOPE -- never
        "shared". Defaulting to shared would silently reproduce the
        pre-Stage-2 cross-session leak; a caller that wants real
        isolation from other callers must pass an explicit scope (e.g.
        their chat session id) or "shared" explicitly.
        """
        if file_type == "url":
            # SSRF guard: url_loader.py is a synthetic stub today (no real
            # fetch), but this validates at the boundary that would
            # perform a future real fetch, so the protection is already
            # in place once that happens.
            validate_url(source)
        resolved_scope = resolve_scope(scope)
        docs = self.processor.load(source, file_type, display_name=display_name)
        chunks = self.optimizer.split(docs, file_type)
        for chunk in chunks:
            chunk.metadata["scope"] = resolved_scope
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
            "scope": resolved_scope,
        }

    def auto_ingest(self, data_dir: Path, extensions: tuple[str, ...]) -> dict:
        """Bulk-ingest the local data_dir as the curated shared corpus.

        Unlike ingest(), this defaults to SHARED_SCOPE rather than a
        private session scope: data_dir is server-side curated content
        every session should be able to reach, not private uploads.
        """
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
                result = self.ingest(str(path), file_type, scope=SHARED_SCOPE)
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
