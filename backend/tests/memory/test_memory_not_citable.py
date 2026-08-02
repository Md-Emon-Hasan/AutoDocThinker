"""Memory must not be citable as a document source: Stage 3's mechanical
citation check must reject a citation pointing at a memory record.

This holds structurally: format_memory_section() never assigns facts a
numeric id the way build_sources() does for context_docs, so a memory
fact can never appear in the ``sources`` list the Verifier validates
citations against.
"""

from app.memory.retrieval import format_memory_section
from app.rag.citations import build_sources
from app.verification.citations import mechanical_check


class _Fact:
    def __init__(self, text):
        self.text = text


class TestMemoryNotCitable:
    def test_memory_section_has_no_citation_markers(self):
        section = format_memory_section([_Fact("the user prefers dark mode")])
        assert "[1]" not in section

    def test_citation_pointing_at_memory_position_is_rejected(self):
        # Only one real document source exists (id=1). An answer citing
        # [2] -- as if a memory fact were a second numbered source --
        # must be flagged as invalid by the mechanical check.
        sources = build_sources([_DocLike()])
        issues = mechanical_check(
            "The user prefers dark mode [2], based on the document [1].", sources
        )
        assert any("[2]" in issue for issue in issues)

    def test_memory_section_appended_to_context_not_sources(self):
        """The memory section is concatenated into the context text
        RAGService builds (see _memory_augmented_formatter), never into
        the `sources` list docs are numbered from -- so it structurally
        cannot receive a citation id."""
        from app.rag.formatting import format_context_with_sources

        context, sources = format_context_with_sources([_DocLike()])
        augmented = context + format_memory_section([_Fact("a remembered fact")])
        assert len(sources) == 1  # memory added no new source entries
        assert "a remembered fact" in augmented


class _DocLike:
    page_content = "document content"
    metadata = {"source": "doc.txt", "chunk_id": "c1"}
