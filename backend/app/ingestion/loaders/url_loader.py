from app.ingestion.document import Document
from app.ingestion.loaders.base import BaseLoader


class UrlLoader(BaseLoader):
    def load(self, source: str) -> list[Document]:
        return [Document(f"Web source: {source}", {"source": source})]
