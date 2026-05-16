"""Consolidated tests for utility modules."""

import pytest

from app.schemas.common import MessageOut
from app.utils.hashing import sha1_short
from app.utils.retry import should_retry
from app.utils.serialization import to_dict
from app.utils.testing import fake_history
from app.utils.text import normalize_space
from app.utils.time import utc_now_iso
from app.utils.validation import require_non_empty


class TestUtils:
    def test_sha1_short(self):
        assert len(sha1_short("abc", 6)) == 6

    def test_normalize_space(self):
        assert normalize_space("a   b") == "a b"

    def test_utc_now_iso(self):
        assert "T" in utc_now_iso()

    def test_should_retry(self):
        assert should_retry(1, 2) is True
        assert should_retry(2, 2) is False

    def test_to_dict_pydantic(self):
        assert to_dict(MessageOut(message="ok"))["message"] == "ok"

    def test_to_dict_dict(self):
        assert to_dict({"a": 1}) == {"a": 1}

    def test_fake_history(self):
        assert fake_history()[0]["role"] == "user"

    def test_require_non_empty_valid(self):
        assert require_non_empty("x", "name") == "x"

    def test_require_non_empty_raises(self):
        with pytest.raises(ValueError, match="name is required"):
            require_non_empty(" ", "name")
