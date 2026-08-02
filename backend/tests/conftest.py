"""Root-level conftest: shared fixtures for the entire test suite."""

import os

import pytest

# Ensure GROQ_API_KEY is always set BEFORE any app imports
os.environ.setdefault("GROQ_API_KEY", "test-key-for-pytest")
# Admin-protected endpoints refuse outright when unset -- give the whole
# test suite a stable token so those routes are reachable in tests.
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token-for-pytest")

from unittest.mock import MagicMock, patch  # noqa: E402

from app.dependencies import container  # noqa: E402
from app.governance.audit import AuditLog  # noqa: E402
from app.hitl.store import HITLStore  # noqa: E402
from app.indexing.chroma_store import ChromaStore  # noqa: E402
from app.indexing.hybrid_index import HybridIndex  # noqa: E402
from app.ingestion.document import Document  # noqa: E402
from app.memory.semantic import FactIndex  # noqa: E402
from app.memory.store import MemoryStore  # noqa: E402
from app.orchestration.scratchpad import ScratchpadStore  # noqa: E402
from app.rag.formatting import format_context_with_sources  # noqa: E402

ADMIN_TOKEN_HEADER = {"X-Admin-Token": "test-admin-token-for-pytest"}


class _FakeGroqClient:
    """Stub GroqClient that never calls the real Groq API."""

    def __init__(self, model: str | None = None):
        self._model = model or "test-model"

    def answer(self, question: str, context: str, domain_prompt: str) -> str:
        return f"mock answer for: {question}"


@pytest.fixture(autouse=True)
def _patch_groq():
    """Patch GroqClient everywhere so tests never hit the real API."""
    with (
        patch("app.llm.groq_client.Groq"),
        patch("app.dependencies.GroqClient", _FakeGroqClient),
    ):
        yield


@pytest.fixture(autouse=True)
def reset_container():
    """Clear the LRU-cached DI container before and after every test."""
    container.cache_clear()
    yield
    container.cache_clear()


@pytest.fixture(autouse=True)
def _isolate_chroma_store(tmp_path, monkeypatch):
    """Point ChromaStore's default persist directory at a per-test tmp dir.

    Without this, the dense store's on-disk Chroma collection would persist
    across tests (unlike the in-memory HybridIndex, which is fresh every
    test), leaking one test's ingested documents into another's dense
    search results, and would grow an on-disk directory in the real repo
    on every test run.
    """
    original_init = ChromaStore.__init__
    chroma_dir = tmp_path / "chroma"

    def _scoped_init(
        self, domain="general", persist_directory=None, cache_manager=None
    ):
        original_init(
            self,
            domain=domain,
            persist_directory=persist_directory or chroma_dir,
            cache_manager=cache_manager,
        )

    monkeypatch.setattr(ChromaStore, "__init__", _scoped_init)
    yield


@pytest.fixture(autouse=True)
def _isolate_governance_and_hitl_stores(tmp_path, monkeypatch):
    """Point AuditLog/HITLStore's SQLite files at a per-test tmp dir.

    Without this, every test touching container() would write real
    governance_audit.sqlite3/hitl.sqlite3 files into the repo's data/
    directory -- the same pollution problem Stage 0 fixed for ChromaDB.
    """
    original_audit_init = AuditLog.__init__
    original_hitl_init = HITLStore.__init__
    audit_path = tmp_path / "governance_audit.sqlite3"
    hitl_path = tmp_path / "hitl.sqlite3"

    def _scoped_audit_init(self, db_path=None):
        original_audit_init(self, db_path or audit_path)

    def _scoped_hitl_init(self, db_path=None):
        original_hitl_init(self, db_path or hitl_path)

    monkeypatch.setattr(AuditLog, "__init__", _scoped_audit_init)
    monkeypatch.setattr(HITLStore, "__init__", _scoped_hitl_init)
    yield


@pytest.fixture(autouse=True)
def _isolate_memory_stores(tmp_path, monkeypatch):
    """Point MemoryStore's SQLite file and FactIndex's Chroma dir at a
    per-test tmp dir, for the same reasons as the fixtures above."""
    original_memory_init = MemoryStore.__init__
    original_fact_index_init = FactIndex.__init__
    memory_db_path = tmp_path / "memory.sqlite3"
    fact_index_dir = tmp_path / "chroma_memory"

    def _scoped_memory_init(self, db_path=None):
        original_memory_init(self, db_path or memory_db_path)

    def _scoped_fact_index_init(self, persist_directory=None, cache_manager=None):
        original_fact_index_init(
            self,
            persist_directory=persist_directory or fact_index_dir,
            cache_manager=cache_manager,
        )

    monkeypatch.setattr(MemoryStore, "__init__", _scoped_memory_init)
    monkeypatch.setattr(FactIndex, "__init__", _scoped_fact_index_init)
    yield


@pytest.fixture(autouse=True)
def _isolate_scratchpad_store(tmp_path, monkeypatch):
    """Point ScratchpadStore's SQLite file at a per-test tmp dir."""
    original_init = ScratchpadStore.__init__
    scratchpad_path = tmp_path / "scratchpad.sqlite3"

    def _scoped_init(self, db_path=None):
        original_init(self, db_path or scratchpad_path)

    monkeypatch.setattr(ScratchpadStore, "__init__", _scoped_init)
    yield


@pytest.fixture()
def fresh_index():
    """Return a brand-new empty HybridIndex."""
    return HybridIndex()


@pytest.fixture()
def sample_document():
    """Return a single Document with minimal metadata."""
    return Document(
        "alpha beta gamma delta",
        {"source_id": "src1", "chunk_id": "c1"},
    )


@pytest.fixture()
def sample_documents():
    """Return a list of Documents for indexing tests."""
    return [
        Document(
            "alpha beta " * 100,
            {"source_id": "s1", "chunk_id": "1", "kind": "a"},
        ),
        Document(
            "beta gamma",
            {"source_id": "s2", "chunk_id": "2", "kind": "b"},
        ),
    ]


@pytest.fixture()
def populated_index(fresh_index, sample_documents):
    """Return an index pre-loaded with sample_documents."""
    fresh_index.add(sample_documents)
    return fresh_index


@pytest.fixture()
def rag_state():
    """Return a minimal RAG state dict for workflow tests."""
    return {
        "input": "payment terms",
        "formatter": format_context_with_sources,
        "metadata_filter": None,
    }


@pytest.fixture()
def seeded_container(tmp_path):
    """Container with a text document already ingested."""
    box = container()
    source = tmp_path / "general.txt"
    source.write_text("payment terms are net thirty days", encoding="utf-8")
    box["ingestion"].ingest(str(source), "txt")
    return box
