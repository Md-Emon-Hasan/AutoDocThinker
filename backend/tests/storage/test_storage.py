"""Consolidated tests for storage module."""

from app.storage.cleanup import removable
from app.storage.file_storage import save_text
from app.storage.paths import ensure_dir
from app.storage.upload_storage import upload_path
from app.storage.vector_storage import vector_path


class TestStorage:
    def test_ensure_dir(self, tmp_path):
        folder = tmp_path / "x"
        assert not folder.exists()
        ensure_dir(folder)
        assert folder.is_dir()

    def test_save_text_and_removable(self, tmp_path):
        folder = ensure_dir(tmp_path / "x")
        fp = save_text(folder / "a.txt", "hi")
        assert fp.exists() and removable(fp)

    def test_removable_missing(self, tmp_path):
        assert not removable(tmp_path / "missing.txt")

    def test_upload_path(self, tmp_path):
        assert upload_path(tmp_path, "b.txt").name == "b.txt"

    def test_vector_path(self, tmp_path):
        assert vector_path(tmp_path, "col").name == "col"
