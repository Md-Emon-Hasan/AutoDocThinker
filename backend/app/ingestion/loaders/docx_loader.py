from app.ingestion.document import Document
from app.ingestion.loaders.base import BaseLoader


class DocxLoader(BaseLoader):
    def load(self, source: str) -> list[Document]:
        try:
            import docx2txt
        except Exception as exc:
            raise RuntimeError("DOCX loading requires docx2txt") from exc
        return [Document(docx2txt.process(source) or "")]
