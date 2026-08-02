"""Four-layer TTL cache: embeddings, reranking, query->answer, wikipedia.

Each layer is a separate cachetools.TTLCache instance with its own
TTL/maxsize, guarded by its own threading.Lock (TTLCache is not
thread-safe and requests run in FastAPI's threadpool). CACHE_ENABLED
(via RAGConfig.cache_enabled) makes every layer a transparent
pass-through when disabled.
"""

import threading
from dataclasses import dataclass
from typing import Any

from cachetools import TTLCache

from app.core.config import RAGConfig

MISSING = object()


class TTLCacheLayer:
    """One named cache layer: thread-safe get/set/stats/clear."""

    def __init__(self, maxsize: int, ttl: float) -> None:
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: Any) -> Any:
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return MISSING

    def set(self, key: Any, value: Any) -> None:
        # Never cache a failure: None, empty containers, or missing values.
        if value is None:
            return
        with self._lock:
            self._cache[key] = value

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        with self._lock:
            size = len(self._cache)
            maxsize = self._cache.maxsize
            ttl = self._cache.ttl
            hits, misses = self._hits, self._misses
        total = hits + misses
        return {
            "size": size,
            "maxsize": maxsize,
            "ttl": ttl,
            "hits": hits,
            "misses": misses,
            "hit_rate": (hits / total) if total else 0.0,
        }


class _PassthroughLayer:
    """Used when caching is disabled: every get is a miss, set is a no-op."""

    def get(self, key: Any) -> Any:
        return MISSING

    def set(self, key: Any, value: Any) -> None:
        return None

    def clear(self) -> None:
        return None

    def stats(self) -> dict:
        return {
            "size": 0,
            "maxsize": 0,
            "ttl": 0,
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
        }


@dataclass
class CacheManager:
    """Holds the four cache layers and enable/disable state."""

    enabled: bool
    embeddings: Any
    rerank: Any
    answer: Any
    wikipedia: Any

    _LAYER_NAMES = ("embeddings", "rerank", "answer", "wikipedia")

    @classmethod
    def from_config(cls, config: RAGConfig) -> "CacheManager":
        if not config.cache_enabled:
            passthrough = _PassthroughLayer()
            return cls(
                enabled=False,
                embeddings=passthrough,
                rerank=passthrough,
                answer=passthrough,
                wikipedia=passthrough,
            )
        return cls(
            enabled=True,
            embeddings=TTLCacheLayer(
                config.embedding_cache_maxsize, config.embedding_cache_ttl
            ),
            rerank=TTLCacheLayer(config.rerank_cache_maxsize, config.rerank_cache_ttl),
            answer=TTLCacheLayer(config.answer_cache_maxsize, config.answer_cache_ttl),
            wikipedia=TTLCacheLayer(
                config.wikipedia_cache_maxsize, config.wikipedia_cache_ttl
            ),
        )

    def clear_all_caches(self) -> None:
        for name in self._LAYER_NAMES:
            getattr(self, name).clear()

    def clear_layer(self, name: str) -> None:
        if name not in self._LAYER_NAMES:
            raise KeyError(f"Unknown cache layer: {name}")
        getattr(self, name).clear()

    def cache_stats(self) -> dict:
        return {name: getattr(self, name).stats() for name in self._LAYER_NAMES}
