"""A deterministic, dependency-free embedding function for ChromaDB.

Chroma's bundled "default" embedding function downloads an ONNX MiniLM
model from the network on first use. That violates the test suite's
no-network-calls constraint and is far too slow to construct once per test
(confirmed empirically: initialization did not complete within two
minutes). This hashing-trick embedding function needs no model download,
no torch/sentence-transformers dependency, and no network access, while
still producing genuine (if semantically weak) dense vectors that Chroma
can index and query like any other embedding.
"""

import hashlib
import math

from chromadb.api.types import Documents
from chromadb.api.types import EmbeddingFunction as ChromaEmbeddingFunction
from chromadb.api.types import Embeddings

from app.indexing.tokenizer import tokenize

DEFAULT_DIMENSIONS = 256


class HashingEmbeddingFunction(ChromaEmbeddingFunction):
    """Bag-of-hashed-tokens embedding, L2-normalized."""

    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS) -> None:
        self._dimensions = dimensions

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed(text) for text in input]

    @classmethod
    def name(cls) -> str:
        return "autodocthinker-hashing-embedding"

    @staticmethod
    def build_from_config(config: dict) -> "HashingEmbeddingFunction":
        return HashingEmbeddingFunction(
            dimensions=config.get("dimensions", DEFAULT_DIMENSIONS)
        )

    def get_config(self) -> dict:
        return {"dimensions": self._dimensions}

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            vector[int(digest, 16) % self._dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
