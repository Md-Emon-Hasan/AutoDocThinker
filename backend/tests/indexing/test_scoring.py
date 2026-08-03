"""Consolidated tests for indexing and retrieval modules."""

import pytest

from app.retrieval.scoring import combine_scores


class TestScoring:
    def test_weighted(self):
        assert combine_scores(1.0, 0.0, 0.5) == 0.5

    def test_equal(self):
        assert combine_scores(0.8, 0.8) == pytest.approx(0.8)
