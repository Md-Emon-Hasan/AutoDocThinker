"""Tests for app/utils/cache.py: the four-layer TTL cache."""

import time

import pytest

from app.core.config import RAGConfig
from app.utils.cache import MISSING, CacheManager, TTLCacheLayer


class TestTTLCacheLayer:
    def test_miss_then_hit(self):
        layer = TTLCacheLayer(maxsize=10, ttl=60)
        assert layer.get("k") is MISSING
        layer.set("k", "v")
        assert layer.get("k") == "v"

    def test_none_is_never_cached(self):
        layer = TTLCacheLayer(maxsize=10, ttl=60)
        layer.set("k", None)
        assert layer.get("k") is MISSING

    def test_stats_track_hits_and_misses(self):
        layer = TTLCacheLayer(maxsize=10, ttl=60)
        layer.get("missing")
        layer.set("k", "v")
        layer.get("k")
        layer.get("k")
        stats = layer.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["maxsize"] == 10
        assert stats["hit_rate"] == 2 / 3

    def test_clear_resets_size_and_counters(self):
        layer = TTLCacheLayer(maxsize=10, ttl=60)
        layer.set("k", "v")
        layer.get("k")
        layer.get("missing")
        layer.clear()
        stats = layer.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_ttl_expiry(self):
        layer = TTLCacheLayer(maxsize=10, ttl=0.05)
        layer.set("k", "v")
        assert layer.get("k") == "v"
        time.sleep(0.1)
        assert layer.get("k") is MISSING


class TestCacheManager:
    def test_four_layers_are_independent(self):
        manager = CacheManager.from_config(RAGConfig())
        manager.embeddings.set("k", [1.0])
        assert manager.rerank.get("k") is MISSING
        assert manager.answer.get("k") is MISSING
        assert manager.wikipedia.get("k") is MISSING
        assert manager.embeddings.get("k") == [1.0]

    def test_clear_all_caches(self):
        manager = CacheManager.from_config(RAGConfig())
        manager.embeddings.set("k", [1.0])
        manager.rerank.set("k", 0.5)
        manager.answer.set("k", {"answer": "a"})
        manager.wikipedia.set("k", "doc")
        manager.clear_all_caches()
        assert manager.embeddings.get("k") is MISSING
        assert manager.rerank.get("k") is MISSING
        assert manager.answer.get("k") is MISSING
        assert manager.wikipedia.get("k") is MISSING

    def test_clear_single_layer(self):
        manager = CacheManager.from_config(RAGConfig())
        manager.embeddings.set("k", [1.0])
        manager.rerank.set("k", 0.5)
        manager.clear_layer("embeddings")
        assert manager.embeddings.get("k") is MISSING
        assert manager.rerank.get("k") == 0.5

    def test_clear_unknown_layer_raises(self):
        manager = CacheManager.from_config(RAGConfig())
        with pytest.raises(KeyError):
            manager.clear_layer("nonexistent")

    def test_cache_stats_reports_all_layers(self):
        manager = CacheManager.from_config(RAGConfig())
        stats = manager.cache_stats()
        assert set(stats.keys()) == {"embeddings", "rerank", "answer", "wikipedia"}
        for layer_stats in stats.values():
            assert set(layer_stats.keys()) == {
                "size",
                "maxsize",
                "ttl",
                "hits",
                "misses",
                "hit_rate",
            }

    def test_disabled_config_makes_every_layer_passthrough(self):
        manager = CacheManager.from_config(RAGConfig(cache_enabled=False))
        assert manager.enabled is False
        manager.answer.set("k", {"answer": "a"})
        assert manager.answer.get("k") is MISSING
        manager.clear_all_caches()
        assert manager.answer.stats()["size"] == 0
