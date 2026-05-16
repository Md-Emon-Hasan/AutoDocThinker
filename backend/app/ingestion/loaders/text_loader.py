from app.ingestion.document import Document
from app.ingestion.loaders.base import BaseLoader


class TextLoader(BaseLoader):
    def load(self, source: str) -> list[Document]:
        if not source.strip():
            raise ValueError("Text content is empty")
        return [Document(source)]
