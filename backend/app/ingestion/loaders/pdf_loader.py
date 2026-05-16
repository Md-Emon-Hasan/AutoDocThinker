from app.ingestion.document import Document
from app.ingestion.loaders.base import BaseLoader


class PdfLoader(BaseLoader):
    def load(self, source: str) -> list[Document]:
        try:
            import fitz
        except Exception as exc:
            raise RuntimeError("PDF loading requires pymupdf") from exc
        with fitz.open(source) as pdf:
            return [
                Document(page.get_text(), {"page": number + 1})
                for number, page in enumerate(pdf)
            ]
