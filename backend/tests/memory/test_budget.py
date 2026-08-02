"""Tests for app/memory/retrieval.py: token cap and ranking.

Caps injected memory by TOKEN COUNT, not record count, and ranks by
relevance x recency x confidence -- without a hard budget, prompts grow
unbounded and every query gets slower and costlier.
"""

from app.memory.retrieval import format_memory_section, select_facts_within_budget


class _Fact:
    def __init__(self, text, confidence, updated_at):
        self.text = text
        self.confidence = confidence
        self.updated_at = updated_at


class TestTokenBudget:
    def test_caps_by_token_count_not_record_count(self):
        now = 1_000_000.0
        facts = [_Fact("x" * 400, 0.9, now) for _ in range(10)]
        # ~100 tokens each at 4 chars/token; budget only fits ~2.
        selected = select_facts_within_budget(facts, token_budget=250, now=now)
        assert len(selected) < len(facts)

    def test_all_facts_fit_when_budget_is_large(self):
        now = 1_000_000.0
        facts = [_Fact("short fact", 0.9, now) for _ in range(3)]
        selected = select_facts_within_budget(facts, token_budget=10_000, now=now)
        assert len(selected) == 3

    def test_empty_facts_returns_empty(self):
        assert select_facts_within_budget([], token_budget=100) == []


class TestRanking:
    def test_higher_confidence_ranked_first(self):
        now = 1_000_000.0
        low = _Fact("low confidence fact", 0.1, now)
        high = _Fact("high confidence fact", 0.99, now)
        selected = select_facts_within_budget([low, high], token_budget=10, now=now)
        assert selected[0] is high

    def test_more_recent_ranked_first_at_equal_confidence(self):
        now = 1_000_000.0
        old = _Fact("old fact", 0.9, now - 100_000)
        recent = _Fact("recent fact", 0.9, now - 10)
        selected = select_facts_within_budget([old, recent], token_budget=10, now=now)
        assert selected[0] is recent


class TestMemorySectionFormatting:
    def test_empty_facts_produces_empty_section(self):
        assert format_memory_section([]) == ""

    def test_section_is_clearly_delimited(self):
        section = format_memory_section([_Fact("likes tea", 0.9, 0)])
        assert "REMEMBERED CONTEXT" in section
        assert "likes tea" in section
