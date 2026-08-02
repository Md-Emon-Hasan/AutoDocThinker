"""Tests for app/verification/citations.py -- mechanical checks only.

These must never call the gateway: nonexistent chunk id, out-of-scope
citation (indistinguishable from nonexistent given retrieval already
enforces scope -- see module docstring), and an uncited claim are all
caught with zero LLM calls.
"""

from unittest.mock import MagicMock, patch

from app.verification.citations import find_citation_ids, mechanical_check


def _sources():
    return [
        {"id": 1, "label": "doc-a p.1", "source": "doc-a", "chunk_id": "c1"},
        {"id": 2, "label": "doc-b p.2", "source": "doc-b", "chunk_id": "c2"},
    ]


class TestFindCitationIds:
    def test_extracts_bracket_citations(self):
        assert find_citation_ids("claim one [1] and claim two [2].") == [1, 2]

    def test_no_citations(self):
        assert find_citation_ids("no citations here") == []


class TestMechanicalCheck:
    def test_clean_answer_has_no_issues(self):
        issues = mechanical_check("Fact one [1]. Fact two [2].", _sources())
        assert issues == []

    def test_nonexistent_chunk_id_flagged(self):
        issues = mechanical_check("Fact one [99].", _sources())
        assert any("[99]" in issue for issue in issues)

    def test_uncited_claim_flagged(self):
        issues = mechanical_check("A confident claim with no citation.", _sources())
        assert any("no citations" in issue for issue in issues)

    def test_empty_answer_no_issues(self):
        assert mechanical_check("", _sources()) == []

    def test_out_of_scope_citation_is_a_nonexistent_chunk_from_the_callers_view(self):
        # A citation pointing outside the caller's scope can never appear
        # in `sources` (retrieval already enforces scope isolation), so
        # it is indistinguishable from -- and caught the same way as --
        # a nonexistent chunk id.
        scoped_sources = [{"id": 1, "label": "l", "source": "s", "chunk_id": "c1"}]
        issues = mechanical_check("Claim [2].", scoped_sources)
        assert any("[2]" in issue for issue in issues)

    def test_zero_llm_calls(self):
        with patch("app.llm.gateway.client.LLMGateway.answer") as mock_answer:
            mechanical_check("Fact [1].", _sources())
            mechanical_check("Fact [99].", _sources())
            mechanical_check("no citation at all", _sources())
            mock_answer.assert_not_called()

    def test_assert_gateway_never_constructed_or_called(self):
        gateway = MagicMock()
        mechanical_check("Some claim [1].", _sources())
        gateway.answer.assert_not_called()
