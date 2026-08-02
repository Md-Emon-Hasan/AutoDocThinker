from app.ingestion.document import Document
from app.utils.cache import MISSING
from app.utils.hashing import sha1_short


class WikipediaClient:
    """Stage 2: accepts an optional cache layer for repeated topics.

    search() is a synthetic stub today (no real network call), so
    caching mainly protects a *future* real Wikipedia API call from
    rate limiting, per the spec -- there's no real external cost to
    save yet, but the wiring is in place for when there is.
    """

    def __init__(self, cache=None) -> None:
        self._cache = cache

    def search(self, query: str) -> Document:
        cache_key = None
        if self._cache is not None:
            cache_key = sha1_short(query.strip().lower())
            cached = self._cache.get(cache_key)
            if cached is not MISSING:
                return cached

        doc = Document(
            f"Wikipedia fallback summary for {query}",
            {"source": "Wikipedia", "source_id": "wikipedia", "file_type": "web"},
        )
        if self._cache is not None:
            self._cache.set(cache_key, doc)
        return doc
