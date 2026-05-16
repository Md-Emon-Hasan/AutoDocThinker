from app.ingestion.document import Document


class ChunkOptimizer:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, documents: list[Document], file_type: str) -> list[Document]:
        size = (
            1200
            if file_type == "pdf"
            else 800 if file_type == "url" else self.chunk_size
        )
        overlap = min(self.chunk_overlap, max(size // 4, 0))
        chunks: list[Document] = []
        for doc in documents:
            text = doc.page_content.strip()
            if not text:
                continue
            step = max(size - overlap, 1)
            for start in range(0, len(text), step):
                chunk_text = text[start : start + size].strip()
                if chunk_text:
                    meta = {**doc.metadata, "chunk_index": len(chunks)}
                    chunks.append(Document(chunk_text, meta))
                if start + size >= len(text):
                    break
        return chunks
