from abc import ABC, abstractmethod

from app.ingestion.document import Document


class BaseLoader(ABC):
    @abstractmethod
    def load(self, source: str) -> list[Document]:
        raise NotImplementedError
