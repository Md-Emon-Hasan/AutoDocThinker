from pathlib import Path

from app.ingestion.document import Document
from app.ingestion.loaders.base import BaseLoader


class TxtLoader(BaseLoader):
    def load(self, source: str) -> list[Document]:
        return [Document(Path(source).read_text(encoding="utf-8"))]
