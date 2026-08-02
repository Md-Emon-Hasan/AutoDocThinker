"""A deterministic, dependency-free embedding function for ChromaDB.

Chroma's bundled default embedding function downloads an ONNX model over
the network on first use, which violates the test suite's no-network
constraint. This hashing-trick function needs no model download and no
torch/sentence-transformers dependency.
"""

import hashlib
import math

from chromadb.api.types import Documents
from chromadb.api.types import EmbeddingFunction as ChromaEmbeddingFunction
from chromadb.api.types import Embeddings

from app.indexing.tokenizer import tokenize
from app.utils.cache import MISSING
from app.utils.hashing import sha1_short

DEFAULT_DIMENSIONS = 256


class HashingEmbeddingFunction(ChromaEmbeddingFunction):
    """Bag-of-hashed-tokens embedding, L2-normalized. Accepts an optional
    cache layer so repeated text skips recomputation."""

    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS, cache=None) -> None:
        self._dimensions = dimensions
        self._cache = cache

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
        cache_key = None
        if self._cache is not None:
            normalized = " ".join(tokenize(text))
            cache_key = f"{sha1_short(normalized)}::{self.name()}::{self._dimensions}"
            cached = self._cache.get(cache_key)
            if cached is not MISSING:
                return cached

        vector = [0.0] * self._dimensions
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            vector[int(digest, 16) % self._dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        result = [v / norm for v in vector]

        if self._cache is not None:
            self._cache.set(cache_key, result)
        return result
